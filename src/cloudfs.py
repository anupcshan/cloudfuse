#!/usr/bin/python
"""CloudFS FUSE filesystem."""

import argparse
import llfuse
from endpoint import EndPoint

# pylint: disable-msg=W0611
from dropbox_endpoint import DropBoxEndPoint
from copy_endpoint import CopyEndPoint
# pylint: enable-msg=W0611

class CloudFSOperations(llfuse.Operations):
    """CloudFS implementation of llfuse Operations class."""
    def __init__(self):
        super(CloudFSOperations, self).__init__()
        EndPoint.load_saved_endpoints()

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

    def check_if_filesystem_exists(self):
        """
        Return true if CloudFS is detected in any of the backend providers.
        """
        for endpoint in EndPoint.get_all_endpoints():
            endpoint.safe_create_filesystem()

        return True

if __name__ == '__main__':
    # pylint: disable-msg=C0103 
    parser = argparse.ArgumentParser(prog='CloudFS')
    parser.add_argument('-c', '--create', action='store_true',
            help='Create a filesystem if it does not exist')
    parser.add_argument('mountpoint', help='Root directory of mounted CloudFS')
    args = parser.parse_args()

    operations = CloudFSOperations()

    if not operations.check_if_filesystem_exists():
        if args.create:
            #TODO: Create filesystem
            pass
        else:
            raise Exception('CloudFS not detected in backend storage providers.'
                    ' Please rerun the command with --create to automatically'
                    ' create a filesystem.')
    
    llfuse.init(operations, args.mountpoint, [ b'fsname=CloudFS' ])
    
    try:
        llfuse.main(single=False)
    except:
        llfuse.close(unmount=False)
        raise

    llfuse.close()
