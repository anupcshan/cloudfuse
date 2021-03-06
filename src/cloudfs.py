#!/usr/bin/python
"""CloudFS FUSE filesystem."""

import argparse
import errno
import llfuse
import logging
import os
import stat
from endpoint import EndPoint
from time import time

# pylint: disable-msg=W0611
from dropbox_endpoint import DropBoxEndPoint
from copy_endpoint import CopyEndPoint
# pylint: enable-msg=W0611

class Inode:
    """ Inode data structure. """
    def __init__(self, _id):
        self.id = _id
        self.name = ''
        self.isDir = True
        self.size = 0
        self.permissions = None
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.atime = self.ctime = self.mtime = time()
        self.children = []
        self.parent = None
        self.version = 1

class FSTree:
    """ Inode tree structure and associated utilities. """
    def __init__(self):
        self.__current_id = 0
        self.inodes = {}
        self.ROOT_INODE = None
        self.inode_open_count = {}

    def generate_root_inode(self):
        if self.ROOT_INODE is not None:
            raise "Attempting to overwrite root inode"

        self.ROOT_INODE = self.new_inode()
        self.ROOT_INODE.parent = self.ROOT_INODE.id
        self.ROOT_INODE.permissions = (stat.S_IRUSR | stat.S_IWUSR |
                stat.S_IRGRP | stat.S_IROTH | stat.S_IFDIR | stat.S_IXUSR |
                stat.S_IXGRP | stat.S_IXOTH)

    def register_root_inode(self, root_inode):
        if self.ROOT_INODE is not None:
            raise "Attempting to overwrite root inode"

        self.ROOT_INODE = root_inode
        self.inodes[root_inode.id] = root_inode
        self.__current_id += 1

    def new_inode(self):
        next_id = self.__get_next_id()
        new_inode = Inode(next_id)
        self.inodes[next_id] = new_inode
        return new_inode

    def __get_next_id(self):
        self.__current_id += 1
        return self.__current_id

    def get_inode_for_id(self, _id):
        print 'Get Inode for id %d' % (_id)
        return self.inodes[_id]

class CloudFSOperations(llfuse.Operations):
    """CloudFS implementation of llfuse Operations class."""
    def __init__(self):
        super(CloudFSOperations, self).__init__()
        EndPoint.load_saved_endpoints()
        self.tree = FSTree()

    def statfs(self):
        stat_ = llfuse.StatvfsData()

        free_bytes = 0
        total_bytes = 0

        for endpoint in EndPoint.get_all_endpoints():
            info = endpoint.get_info()
            free_bytes += info['freeBytes']
            total_bytes += info['totalBytes']

        stat_.f_bsize = 512
        stat_.f_frsize = 512

        size = total_bytes
        stat_.f_blocks = size // stat_.f_frsize
        stat_.f_bfree = free_bytes // stat_.f_frsize
        stat_.f_bavail = stat_.f_bfree

        stat_.f_favail = stat_.f_ffree = stat_.f_files = 10000

        return stat_

    def lookup(self, parent_inode, name):
        print 'Lookup of name %s under parent_inode %d' % (name, parent_inode)
        inode = None
        if name == '.':
            inode = parent_inode
        elif name == '..':
            inode = self.tree.get_inode_for_id(parent_inode).parent
        else:
            parent = self.tree.get_inode_for_id(self.tree.get_inode_for_id(parent_inode).parent)
            for child_id in parent.children:
                child = self.tree.get_inode_for_id(child_id)
                if child.name == name:
                    inode = child.id

        if inode:
            return self.getattr(inode)

        raise(llfuse.FUSEError(errno.ENOENT))

    def opendir(self, inode):
        return inode

    def readdir(self, inode, off):
        print 'Readdir of inode %d at offset %d' % (inode, off)
        node = self.tree.get_inode_for_id(inode)
        
        i = off
        for child_id in node.children[off:]:
            child = self.tree.get_inode_for_id(child_id)
            if child.name.count('/') == 0:
                i += 1
                yield (child.name.replace('/', '//'), self.getattr(child.id), i)

    def getattr(self, inode):
        node = self.tree.get_inode_for_id(inode)
        print 'Calling getattr on inode %d : %s' % (inode, node.name)

        entry = llfuse.EntryAttributes()
        entry.st_ino = inode
        entry.generation = 0
        entry.entry_timeout = 300
        entry.attr_timeout = 300
        entry.st_mode = node.permissions

        if node.isDir:
            entry.st_nlink = len(node.children) + 1
        else:
            entry.st_nlink = 1

        entry.st_uid = node.uid
        entry.st_gid = node.gid
        entry.st_rdev = 0
        entry.st_size = node.size

        entry.st_blksize = 512
        entry.st_blocks = 1
        entry.st_atime = node.atime
        entry.st_mtime = node.mtime
        entry.st_ctime = node.ctime

        return entry

    def setattr(self, inode, attr):
        logging.info('Setattr not implemented: Inode %d' % (inode))
        return self.getattr(inode)

    def open(self, inode, flags):
        print 'Opening file %d with flags %s' % (inode, flags)

        if inode not in self.tree.inode_open_count:
            self.tree.inode_open_count[inode] = 0
        self.tree.inode_open_count[inode] += 1
        return inode

    def access(self, inode, mode, ctx):
        return True

    def create(self, parent_inode_id, name, mode, flags, ctx):
        parent_inode = self.tree.get_inode_for_id(parent_inode_id)
        child_inode = self.tree.new_inode()
        child_inode.parent = parent_inode_id
        child_inode.isDir = False
        child_inode.name = name
        child_inode.permissions = mode
        parent_inode.children.append(child_inode.id)
        self.open(child_inode.id, flags)
        return (child_inode.id, self.getattr(child_inode.id))

    def mkdir(self, parent_inode_id, name, mode, ctx):
        print 'Mkdir: %s in parent %d' % (name, parent_inode_id)
        parent_inode = self.tree.get_inode_for_id(parent_inode_id)
        child_inode = self.tree.new_inode()
        child_inode.parent = parent_inode_id
        child_inode.isDir = True
        child_inode.children = []
        child_inode.name = name
        child_inode.permissions = mode
        parent_inode.children.append(child_inode.id)
        return self.getattr(child_inode.id)

    def auto_create_filesystem(self):
        """
        Automatically setup filesystem structure on backend providers.
        """
        for endpoint in EndPoint.get_all_endpoints():
            endpoint.safe_create_filesystem()

        root = None
        for endpoint in EndPoint.get_all_endpoints():
            x = endpoint.safe_get_root_inode()
            if x is not None:
                logging.info('Found root inode at endpoint %s' % (endpoint))
                if root is None or x.version > root.version:
                    root = x

        if root is None:
            logging.info('Did not find existing root inode pointer on any '
                    'endpoint. Generating new root inode pointer.')
            self.tree.generate_root_inode()
            root = endpoint.create_root_inode(self.tree.ROOT_INODE)
        else:
            self.tree.register_root_inode(root)

if __name__ == '__main__':
    # pylint: disable-msg=C0103 
    parser = argparse.ArgumentParser(prog='CloudFS')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Enable verbose logging')
    parser.add_argument('mountpoint', help='Root directory of mounted CloudFS')
    args = parser.parse_args()

    logLevel = logging.INFO
    if args.verbose:
      logLevel = logging.DEBUG

    logging.basicConfig(level=logLevel)

    operations = CloudFSOperations()
    operations.auto_create_filesystem()
    # TODO: Load filesystem structure from backends and export them
    #       using FUSE.
    
    logging.info('Mounting CloudFS')
    llfuse.init(operations, args.mountpoint, [ b'fsname=CloudFS' ])
    logging.info('Mounted CloudFS at %s' % (args.mountpoint))
    
    try:
        llfuse.main(single=False)
    except:
        llfuse.close(unmount=False)
        raise

    llfuse.close()
