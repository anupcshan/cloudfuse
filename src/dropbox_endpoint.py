#!/usr/bin/python

from endpoint import EndPoint
import httplib
import json
import oauth2 as oauth
import time
import urlparse

# Figure out a way to store these securely instead of having it open on github.
CONSUMER_KEY = 'oozzv31vqhn0fm5'
CONSUMER_SECRET = 'vmy8fa4jbtb0jw0'

ACCESS_TOKEN_URL = 'https://api.dropbox.com/1/oauth/access_token'
AUTHORIZE_URL = 'https://www.dropbox.com/1/oauth/authorize'
GETINFO_URL = 'https://api.dropbox.com/1/account/info'
REQUEST_TOKEN_URL = 'https://api.dropbox.com/1/oauth/request_token'

class DropBoxEndPoint(EndPoint):
    def __init__(self, configDir = None):
        EndPoint.__init__(self, configDir)
        self._access_token = None
        self._consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
        self._connection = httplib.HTTPSConnection('api.dropbox.com')

    def authenticate(self):
        if self._access_token is not None:
            return

        client = oauth.Client(self._consumer)
        resp, content = client.request(REQUEST_TOKEN_URL, 'GET')

        if resp['status'] != '200':
            raise Exception('Invalid response %s.' % resp)

        request_token = dict(urlparse.parse_qsl(content))

        print 'Go to the following link in your browser:'
        print '%s?oauth_token=%s' % (AUTHORIZE_URL, request_token['oauth_token'])
        print

        accepted = 'n'
        while accepted.lower() == 'n':
            accepted = raw_input('Have you authorized me? (y/n) ')

        token = oauth.Token(request_token['oauth_token'],
                request_token['oauth_token_secret'])
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

        self._connection.request('GET', GETINFO_URL, headers=req.to_header())
        response = self._connection.getresponse()
        info = json.loads(response.read())
        userInfo = {
            'uid': info['uid'],
            'uname': info['email'],
            'totalBytes': info['quota_info']['quota'],
            'usedBytes': info['quota_info']['shared'] + info['quota_info']['normal']
        }
        userInfo['freeBytes'] = userInfo['totalBytes'] - userInfo['usedBytes']
        print userInfo

    def getProviderId(self):
        return "dropbox.v1"

if __name__ == '__main__':
    dbep = DropBoxEndPoint()
    dbep.authenticate()
    dbep.getInfo()
