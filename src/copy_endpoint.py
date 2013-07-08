#!/usr/bin/python

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

class CopyEndPoint(EndPoint):
    def __init__(self, configDir = None):
        EndPoint.__init__(self, configDir)
        self._access_token = None
        self._consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
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
        print '%s?oauth_token=%s' % (AUTHORIZE_URL, request_token['oauth_token'])
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

    def getInfo(self):
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': self._access_token['oauth_token'],
            'oauth_consumer_key': CONSUMER_KEY
        }

        token = oauth.Token(key=self._access_token['oauth_token'],
                secret=self._access_token['oauth_token_secret'])
        req = oauth.Request(method='GET', url=GETINFO_URL, parameters=params)
        signature_method = oauth.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, self._consumer, token)

        print req.to_header()
        self._connection.request('GET', GETINFO_URL, headers=req.to_header())
        response = self._connection.getresponse().read()
        print response

        # FIXME: Figure out why we're getting an empty response.
        info = json.loads(response)
        userInfo = {
            'uid': info['uid'],
            'uname': info['email'],
            'totalBytes': info['quota_info']['quota'],
            'usedBytes': info['quota_info']['shared'] + info['quota_info']['normal']
        }
        userInfo['freeBytes'] = userInfo['totalBytes'] - userInfo['usedBytes']
        print userInfo

    @classmethod
    def getProviderId(self):
        return "copy.v1"

CopyEndPoint.registerEndPoint()

if __name__ == '__main__':
    cep = CopyEndPoint()
    cep.authenticate()
    cep.getInfo()
