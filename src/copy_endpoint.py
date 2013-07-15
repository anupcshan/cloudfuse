#!/usr/bin/python
"""Cloud endpoint which talks to copy.com"""

from endpoint import EndPoint
import httplib
import json
import oauth2 as oauth
import time
import urlparse
import urllib

# Figure out a way to store these securely instead of having it open on github.
CONSUMER_KEY = 'L9dKepamNkSfkkAGA2TGCFr750cOFc0b'
CONSUMER_SECRET = 'Qd6IHqkejU1bzpslxvEpz4X4pUc2iG0gpDpzfrqrkHCsE8Qv'

ACCESS_TOKEN_URL = 'https://api.copy.com/oauth/access'
AUTHORIZE_URL = 'https://www.copy.com/applications/authorize'
GETINFO_URL = 'https://api.copy.com/rest/user'
REQUEST_TOKEN_URL = 'https://api.copy.com/oauth/request'
GET_PATH_METADATA_URL = 'https://api.copy.com/rest/meta/copy/%s'
CREATE_FOLDER_URL = 'https://api.copy.com/rest/files/%s'

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
        self._connection = httplib.HTTPSConnection('api.copy.com')

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
        self._connection.request('GET', GETINFO_URL,
                headers=self.get_signed_request(GETINFO_URL))
        response = self._connection.getresponse().read()
        print response

        info = json.loads(response)
        user_info = {
            'uid': info['user_id'],
            'uname': info['email'],
            'totalBytes': info['storage']['quota'],
            'usedBytes': info['storage']['used'],
            'freeBytes': 0
        }
        user_info['freeBytes'] = user_info['totalBytes'] - user_info['usedBytes']
        print user_info
        return user_info

    def load_credentials(self, credentials):
        self._access_token = credentials

    def if_file_exists(self, path):
        url = GET_PATH_METADATA_URL % path
        self._connection.request('GET', url,
                headers=self.get_signed_request(url))
        response = self._connection.getresponse().read()
        info = json.loads(response)
        print info

        if 'type' in info and info['type'] == 'file' and 'error' not in info:
            return True

        return False

    def if_folder_exists(self, path):
        url = GET_PATH_METADATA_URL % path
        self._connection.request('GET', url,
                headers=self.get_signed_request(url))
        response = self._connection.getresponse().read()
        info = json.loads(response)
        print info

        if 'type' in info and info['type'] == 'dir' and 'error' not in info:
            return True

        return False

    def create_folder(self, path):
        url = CREATE_FOLDER_URL % path
        print url
        self._connection.request('POST', url,
                headers=self.get_signed_request(url, 'POST'))
        response = self._connection.getresponse().read()
        info = json.loads(response)
        print info

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
