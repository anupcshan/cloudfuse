#!/usr/bin/python

import llfuse
import sys
from endpoint import EndPoint
from dropbox_endpoint import DropBoxEndPoint
from copy_endpoint import CopyEndPoint

class CloudFSOperations(llfuse.Operations):
    def __init__(self):
        EndPoint.loadSavedEndPoints()

    def statfs(self):
        stat_ = llfuse.StatvfsData()

        stat_.f_bsize = 512
        stat_.f_frsize = 512

        size = 10000000000
        stat_.f_blocks = size // stat_.f_frsize
        stat_.f_bfree = max(size // stat_.f_frsize, 1024)
        stat_.f_bavail = stat_.f_bfree

        inodes = 10000
        stat_.f_files = inodes
        stat_.f_ffree = max(inodes , 100)
        stat_.f_favail = stat_.f_ffree

        return stat_
    pass

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        raise SystemExit('Usage: %s <mountpoint>' % sys.argv[0])
    
    mountpoint = sys.argv[1]
    operations = CloudFSOperations()
    
    llfuse.init(operations, mountpoint, [ b'fsname=cloudfs' ])
    
    try:
        llfuse.main(single=False)
    except:
        llfuse.close(unmount=False)
        raise

    llfuse.close()
