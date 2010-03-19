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
from urllib import urlencode

try:
    from urlparse import parse_qs, parse_qsl
except ImportError:
    from cgi import parse_qs, parse_qsl

REQUEST_TOKEN_URL = 'http://twitter.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://twitter.com/oauth/access_token'
AUTHORIZE_URL = 'http://twitter.com/oauth/authorize'
AUTHENTICATE_URL = 'http://twitter.com/oauth/authenticate'

DEFAULT_HTTP_HEADERS = {
    "User-Agent" : "python-twitapi/0.1 (http://github.com/rlr/python-twitapi)"
}


class NoAuth(object):
    """
    No Authentitcation
    """
    def make_request(self, url, method="GET", body=None, cache=None,
                      timeout=None, proxy_info=None):
        """
        Make a request using no authentication.
        """
        client = httplib2.Http(
                              cache=cache,
                              timeout=timeout,
                              proxy_info=proxy_info
                              )
        
        return client.request(url, method, body)


class BasicAuth(object):
    """
    Basic Authentication
    
    It uses the user's username and password for access to the Twitter API.
    """
    def __init__(self, username, password):
        self.username = username
        self.password = password
    
    def make_request(self, url, method="GET", body=None, cache=None,
                      timeout=None, proxy_info=None):
        """
        Make a request using Basic Authentication using the username
        and passowor provided.
        """
        client = httplib2.Http(
                              cache=cache,
                              timeout=timeout,
                              proxy_info=proxy_info
                              )
        
        client.add_credentials(self.username, self.password)
        return client.request(url, method, body)


class OAuth(object):
    """
    OAuth Authentication
    
    It uses the application's consumer key and secret and user's access token
    key and secret for access to the Twitter API.
    """
    consumer = None
    token = None
    
    def __init__(self, consumer_key, consumer_secret,
                 token=None, token_secret=None):
        self.consumer = oauth2.Consumer(key=consumer_key,
                                         secret=consumer_secret)
        if token and token_secret:
            self.token = {
                           "oauth_token":token, 
                           "oauth_token_secret":token_secret
                           }
        else:
            self.token = None
    
    def get_request_token(self, request_token_url=REQUEST_TOKEN_URL):
        """
        Get the oauth request token.
        """
        client = oauth2.Client(self.consumer)
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
            self.token = token = self.get_request_token()
        
        return "%s?oauth_token=%s" % (authorize_url, token['oauth_token'])

    def get_signin_url(self, token=None, authenticate_url=AUTHENTICATE_URL):
        '''
        Create a URL for the user to sign in to the application with Twitter.
        
        Returns:
          The sign-in URL 
        '''
        if not token:
            self.token = token = self.get_request_token()
        
        return self.get_authorization_url(token, authenticate_url)
    
    def get_access_token(self, oauth_verifier=None,
                         access_token_url=ACCESS_TOKEN_URL):
        """
        Get the access token.
        
        This should be called after user has authorized/authenticated.
        If a PIN was provided, it should be passed as the oauth_verifier.
        """
        token = oauth2.Token(self.token['oauth_token'],
                             self.token['oauth_token_secret'])
        if oauth_verifier:
            token.set_verifier(oauth_verifier)
        
        client = oauth2.Client(self.consumer, token)

        resp, content = client.request(access_token_url, "POST")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        
        return dict(parse_qsl(content))

    def set_token(self, token):
        """
        Set the oauth token.
        """
        self.token = token

    def make_request(self, url, method="GET", body=None, cache=None,
                      timeout=None, proxy_info=None):
        """
        Make a request using OAuth authentication with the consumer key and
        secret and the provided token.
        """
        token = oauth2.Token(self.token['oauth_token'],
                             self.token['oauth_token_secret'])
        client = oauth2.Client(
                              consumer=self.consumer,
                              token=token,
                              cache=cache,
                              timeout=timeout,
                              proxy_info=proxy_info
                              )
        
        return client.request(url, method, body)


class Client(object):
    """
    The Twitter API Client
    
    A Twitter API client that can use Basic Authentication, OAuth, or no
    authentication at all (for the methods that allow that).
    
    To use.....
    """
    auth = None
    base_api_url = None
    base_search_url = None
    cache = None
    timeout = None
    proxy_info = None
    
    def __init__(self, auth=None, base_api_url="http://twitter.com",
                 base_search_url="http://search.twitter.com", cache=None,
                 timeout=None, proxy_info=None):
        if not auth:
            auth = NoAuth()
            
        self.auth = auth
        self.base_api_url = base_api_url
        self.base_search_url = base_search_url
        self.cache = cache
        self.timeout = timeout
        self.proxy_info = proxy_info
    
    def request(self, url, method="GET", body=None):
        """
        Make a request with the provided authentication.
        """
        return self.auth.make_request(url, method, body,
                                 self.cache, self.timeout, self.proxy_info)
    
    def statuses_update(self, status, in_reply_to_status_id=None):
        """
        Updates the authenticating user's status.
        
        Requires the status parameter.
        Request must be a POST.
        
        A status update with text identical to the
        authenticating user's current status will be ignored to prevent duplicates.
        """
        params = { "status": status }
        if in_reply_to_status_id:
            params['in_reply_to_status_id'] = in_reply_to_status_id
            
        return self.request(self.base_api_url+'/statuses/update.json', "POST",
                             urlencode(params))
    
    def users_show(self, user_id=None, screen_name=None):
        """
        Returns extended information of a given user, specified by ID or
        screen name as per the required id parameter. The author's most
        recent status will be returned inline.
        """
        if not user_id and not screen_name:
            raise Exception("A user_id or screen_name must be provided.")
        
        if user_id and screen_name:
            raise Exception("A user_id OR screen_name must be provided.")
        
        params = {}
        if user_id:
            params['user_id'] = user_id
        else:
            params['screen_name'] = screen_name
        
        return self.request(self.base_api_url+'/users/show.json?%s' % urlencode(params), "GET")

    





