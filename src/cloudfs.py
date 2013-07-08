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

        freeBytes = 0
        totalBytes = 0
        usedBytes = 0

        for endpoint in EndPoint.getAllEndPoints():
            info = endpoint.getInfo()
            freeBytes += info['freeBytes']
            totalBytes += info['totalBytes']
            usedBytes += info['usedBytes']

        stat_.f_bsize = 512
        stat_.f_frsize = 512

        size = totalBytes
        stat_.f_blocks = size // stat_.f_frsize
        stat_.f_bfree = freeBytes // stat_.f_frsize
        stat_.f_bavail = stat_.f_bfree

        stat_.f_favail = stat_.f_ffree = stat_.f_files = 10000

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
