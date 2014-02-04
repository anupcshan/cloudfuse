#!/usr/bin/python
"""Cloud endpoint which talks to dropbox.com"""

from endpoint import EndPoint, PathMetadata
import httplib2
import json
import logging
import oauth2 as oauth
import os
import time
import urlparse

# Figure out a way to store these securely instead of having it open on github.
CONSUMER_KEY = 'oozzv31vqhn0fm5'
CONSUMER_SECRET = 'vmy8fa4jbtb0jw0'

ACCESS_TOKEN_URL = 'https://api.dropbox.com/1/oauth/access_token'
AUTHORIZE_URL = 'https://www.dropbox.com/1/oauth/authorize'
GETINFO_URL = 'https://api.dropbox.com/1/account/info'
REQUEST_TOKEN_URL = 'https://api.dropbox.com/1/oauth/request_token'
GET_PATH_METADATA_URL = 'https://api.dropbox.com/1/metadata/dropbox/%s'
CREATE_FOLDER_URL = 'https://api.dropbox.com/1/fileops/create_folder?path=%s&root=dropbox'

class DropBoxEndPoint(EndPoint):
    """
    Dropbox.com endpoint based on documentation at
    https://www.dropbox.com/developers/core/docs.
    """
    def __init__(self, _uuid = None):
        EndPoint.__init__(self, _uuid)
        self._access_token = None
        self._consumer = oauth.Consumer(key=CONSUMER_KEY,
                secret=CONSUMER_SECRET)
        self._connection = httplib2.Http()
        self._logger = logging.getLogger('DropBoxEndPoint')

    def authenticate(self):
        if self._access_token is not None:
            return

        client = oauth.Client(self._consumer)
        resp, content = client.request(REQUEST_TOKEN_URL, 'GET')

        if resp['status'] != '200':
            raise Exception('Invalid response %s.' % resp)

        request_token = dict(urlparse.parse_qsl(content))

        print 'Go to the following link in your browser:'
        print '%s?oauth_token=%s' % (AUTHORIZE_URL,
                request_token['oauth_token'])
        print

        accepted = 'n'
        while accepted.lower() == 'n':
            accepted = raw_input('Have you authorized me? (y/n) ')

        token = oauth.Token(request_token['oauth_token'],
                request_token['oauth_token_secret'])
        client = oauth.Client(self._consumer, token)

        resp, content = client.request(ACCESS_TOKEN_URL, "POST")
        self._access_token = dict(urlparse.parse_qsl(content))
        DropBoxEndPoint.store_credentials(self._access_token, self._uuid)

    def get_info(self):
        info = self._make_request(operation='GetInfo', uri=GETINFO_URL)
        user_info = {
            'uid': info['uid'],
            'uname': info['email'],
            'totalBytes': info['quota_info']['quota'],
            'usedBytes': info['quota_info']['shared'] +
                info['quota_info']['normal']
        }
        user_info['freeBytes'] = user_info['totalBytes'] - user_info['usedBytes']
        self._logger.debug(user_info)
        return user_info

    def load_credentials(self, credentials):
        self._access_token = credentials

    def if_file_exists(self, path):
        url = GET_PATH_METADATA_URL % path
        info = self._make_request(operation='GetMetadata', uri=url)

        if 'is_dir' in info and info['is_dir'] != True and 'error' not in info:
            return True

        return False

    def get_path_metadata(self, path):
        url = GET_PATH_METADATA_URL % path
        info = self._make_request(operation='GetMetadata', uri=url)

        if not info or 'error' in info:
            return None

        pathmetadata = PathMetadata()
        pathmetadata.is_dir = info['is_dir']
        pathmetadata.path = info['path']
        pathmetadata.name = os.path.basename(info['path'])
        pathmetadata.mtime = info['modified']

        if pathmetadata.is_dir:
            pathmetadata.size = 0
        else:
            pathmetadata.size = info['bytes']

        return pathmetadata

    def create_folder(self, path):
        url = CREATE_FOLDER_URL % path
        info = self._make_request(operation='CreateFolder', uri=url, method='POST')
        self._logger.debug(info)

    def get_signed_request(self, url, method='GET'):
        """
        Return signed HTTP request headers as a map.
        """
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': self._access_token['oauth_token'],
            'oauth_consumer_key': CONSUMER_KEY
        }

        token = oauth.Token(key=self._access_token['oauth_token'],
                secret=self._access_token['oauth_token_secret'])
        req = oauth.Request(method=method, url=url, parameters=params)
        signature_method = oauth.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, self._consumer, token)

        headers = req.to_header()
        return headers

    @classmethod
    def get_providerid(cls):
        return "dropbox.v1"

DropBoxEndPoint.register_endpoint()

if __name__ == '__main__':
    # pylint: disable-msg=C0103 
    dbep = DropBoxEndPoint()
    dbep.authenticate()
    dbep.get_info()
