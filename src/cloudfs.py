#!/usr/bin/python

import llfuse
import sys

class CloudFSOperations(llfuse.Operations):
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
