"""
The MIT License

Copyright (c) 2010 Ricky Rosario

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import httplib2
import oauth2

try:
    from urlparse import parse_qs, parse_qsl
except ImportError:
    from cgi import parse_qs, parse_qsl

REQUEST_TOKEN_URL = 'http://twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://twitter.com/oauth/access_token'
AUTHORIZE_URL = 'http://twitter.com/oauth/authorize'
AUTHENTICATE_URL = 'http://twitter.com/oauth/authenticate'

class BasicAuth(object):
    """
    Basic Authentication
    
    It uses the user's username and password for access to the Twitter API.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def make_request(self, url, method, params):
        pass

class OAuth(object):
    """
    OAuth Authentication
    
    It uses the application's consumer key and secret and user's access token
    key and secret for access to the Twitter API.
    """
    _consumer = None
    _token = None
    
    def __init__(self, consumer_key, consumer_secret,
                 token=None, token_secret=None):
        self._consumer = oauth2.Consumer(key=consumer_key,
                                         secret=consumer_secret)
        if token and token_secret:
            self._token = {
                           "oauth_token":token, 
                           "oauth_token_secret":token_secret
                           }
        else:
            self._access_token = None
    
    def get_request_token(self, request_token_url=REQUEST_TOKEN_URL):
        """
        Get the oauth request token.
        """
        client = oauth2.Client(self._consumer)
        resp, content = client.request(request_token_url, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        
        return dict(parse_qsl(content))
    
    def get_authorization_url(self, token=None, authorize_url=AUTHORIZE_URL):
        '''
        Create a URL for the user to authorize the application with the Twitter
        API.
        
        Returns:
          The authorization URL 
        '''
        if not token:
            self._token = token = self.get_request_token()
        
        return "%s?oauth_token=%s" % (authorize_url, token['oauth_token'])

    def get_signin_url(self, token=None, authenticate_url=AUTHENTICATE_URL):
        '''
        Create a URL for the user to sign in to the application with Twitter.
        
        Returns:
          The sign-in URL 
        '''
        return self.get_authorization_url(token, authenticate_url)
    
    def get_access_token(self, oauth_verifier=None,
                         access_token_url=ACCESS_TOKEN_URL):
        """
        Get the access token.
        
        This should be called after user has authorized/authenticated. If a PIN was provided,
        it should be passed as the oauth_verifier.
        """
        token = oauth2.Token(self._token['oauth_token'],
                             self._token['oauth_token_secret'])
        if oauth_verifier:
            token.set_verifier(oauth_verifier)
        
        client = oauth2.Client(self._consumer, token)

        resp, content = client.request(access_token_url, "POST")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        
        return dict(parse_qsl(content))

    def set_token(self, token):
        """
        Set the oauth token.
        """
        self._token = token

    def make_request(self, url, method, params):
        pass




