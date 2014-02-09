#!/usr/bin/python
"""Cloud endpoint which talks to copy.com"""

from endpoint import EndPoint, PathMetadata
import httplib2
import json
import logging
import oauth2 as oauth
import time
import urllib
import urlparse

# Figure out a way to store these securely instead of having it open on github.
CONSUMER_KEY = 'L9dKepamNkSfkkAGA2TGCFr750cOFc0b'
CONSUMER_SECRET = 'Qd6IHqkejU1bzpslxvEpz4X4pUc2iG0gpDpzfrqrkHCsE8Qv'

ACCESS_TOKEN_URL = 'https://api.copy.com/oauth/access'
AUTHORIZE_URL = 'https://www.copy.com/applications/authorize'
GETINFO_URL = 'https://api.copy.com/rest/user'
REQUEST_TOKEN_URL = 'https://api.copy.com/oauth/request'
GET_PATH_METADATA_URL = 'https://api.copy.com/rest/meta/copy/%s'
CREATE_FOLDER_URL = 'https://api.copy.com/rest/files/%s'
CREATE_FILE_URL = 'https://api.copy.com/rest/files/%s'
GET_FILE_URL = 'https://api.copy.com/rest/files/%s'

class CopyEndPoint(EndPoint):
    """
    Copy.com endpoint based on documentation at
    https://www.copy.com/developer/documentation.
    """
    def __init__(self, _uuid = None):
        EndPoint.__init__(self, _uuid)
        self._access_token = None
        self._consumer = oauth.Consumer(key=CONSUMER_KEY,
                secret=CONSUMER_SECRET)
        self._connection = httplib2.Http()
        self._logger = logging.getLogger('CopyEndPoint')

    def authenticate(self):
        if self._access_token is not None:
            return

        client = oauth.Client(self._consumer)
        resp, content = client.request(REQUEST_TOKEN_URL, 'POST',
                body=urllib.urlencode({'oauth_callback':'http://copy.com'}))

        if resp['status'] != '200':
            raise Exception('Invalid response: %s\n%s' % (resp, content))

        request_token = dict(urlparse.parse_qsl(content))

        print 'Go to the following link in your browser:'
        print '%s?oauth_token=%s' % (AUTHORIZE_URL,
                request_token['oauth_token'])
        print

        accepted = 'n'
        while accepted.lower() == 'n':
            accepted = raw_input('Have you authorized me? (y/n) ')
        oauth_verifier = raw_input('What is the verifier id? ')

        token = oauth.Token(request_token['oauth_token'],
                request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self._consumer, token)

        resp, content = client.request(ACCESS_TOKEN_URL, "POST")
        self._access_token = dict(urlparse.parse_qsl(content))
        CopyEndPoint.store_credentials(self._access_token, self._uuid)

    def get_info(self):
        info = self._make_request(operation='GetInfo', uri=GETINFO_URL)
        user_info = {
            'uid': info['user_id'],
            'uname': info['email'],
            'totalBytes': info['storage']['quota'],
            'usedBytes': info['storage']['used'],
            'freeBytes': 0
        }
        user_info['freeBytes'] = user_info['totalBytes'] - user_info['usedBytes']
        self._logger.debug(user_info)
        return user_info

    def load_credentials(self, credentials):
        self._access_token = credentials

    def get_path_metadata(self, path):
        url = GET_PATH_METADATA_URL % path
        info = self._make_request(operation='GetMetadata', uri=url)

        if not info or 'error' in info or 'type' not in info:
            return None

        pathmetadata = PathMetadata()
        pathmetadata.is_dir = info['type'] == 'dir'
        pathmetadata.path = info['path']
        pathmetadata.name = info['name']
        pathmetadata.mtime = info['modified_time']

        if pathmetadata.is_dir:
            pathmetadata.size = 0
        else:
            pathmetadata.size = info['size']

        return pathmetadata

    def create_folder(self, path):
        url = CREATE_FOLDER_URL % path
        info = self._make_request(operation='CreateFolder', uri=url, method='POST')

    def get_file(self, path):
        url = GET_FILE_URL % path
        data = self._make_request(operation='GetFile', uri=url, parse=False)
        return data

    def create_file(self, path, data):
        url = CREATE_FILE_URL % path
        info = self._make_request(operation='CreateFile', uri=url, method='POST', body=data)
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
        headers.update({'X-API-Version': '1.0'})
        return headers

    @classmethod
    def get_providerid(cls):
        return "copy.v1"

CopyEndPoint.register_endpoint()

if __name__ == '__main__':
    # pylint: disable-msg=C0103 
    cep = CopyEndPoint()
    cep.authenticate()
    cep.get_info()
