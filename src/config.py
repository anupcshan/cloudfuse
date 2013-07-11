#!/usr/bin/python
"""Common configuration for cloudfs."""

import os

DEFAULT_CLOUDFS_ROOT = os.environ['HOME'] + '/.cloudfs'

class Config:
    """
    CloudFS configuration.
    """
    def __init__(self):
        self._root = DEFAULT_CLOUDFS_ROOT
        self._credentials_dir = self._root + '/credentials'

    def get_credentials_dir(self):
        # pylint: disable-msg=C0111
        return self._credentials_dir
