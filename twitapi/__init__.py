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
from datetime import date as datetype
try:
    import json # python 2.6
except ImportError:
    import simplejson as json # python 2.4 to 2.5
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
    def make_request(self, url, method="GET", body=None, headers=None,
                     cache=None, timeout=None, proxy_info=None):
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
    
    def make_request(self, url, method="GET", body=None, headers=None,
                     cache=None, timeout=None, proxy_info=None):
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

    def make_request(self, url, method="GET", body=None, headers=None,
                     cache=None, timeout=None, proxy_info=None):
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
    
    def __init__(self, auth=None, base_api_url="http://api.twitter.com/1",
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
    
    def request(self, url, method="GET", body=None, headers=None):
        """
        Make a request with the provided authentication.
        
        The response is assumed to be json and is parsed to a dict that is
        returned along with the response headers. If an exception is caught while
        decoding the json, then the raw response body is returned (should only happen
        if status != '200').
        NOTE: Feels ugly.. Should I be doing this in a different way?
        """
        if headers is None:
            headers = DEFAULT_HTTP_HEADERS.copy()
        
        resp, content = self.auth.make_request(url, method, body, headers,
                                 self.cache, self.timeout, self.proxy_info)
        try:
        	decoded = json.loads(content)
        	content = decoded
        except json.decoder.JSONDecodeError:
            pass
            
        return resp, content
    
    #####################
    # Search API Methods
    #####################
    
    def search(self, q, **kwargs):
        """
        Returns tweets that match a specified query.
        
        See the Twitter Search API documentation for all the parameters:
        http://apiwiki.twitter.com/Twitter-Search-API-Method:-search
        
        Example::

            # create the client (authentication not required for search)
            twitter = Client()
            
            # search for beer
            resp, search_results = twitter.search('beer')
          
        """
        params = kwargs
        if q:
            params['q'] = q
        
        return self.request(self.base_search_url+'/search.json?%s' %
                             urlencode(params), "GET")
    
    def trends(self):
        """
        Returns the top ten topics that are currently trending on Twitter.
        The response includes the time of the request, the name of each
        trend, and the url to the Twitter Search results page for that topic.
        
        Example::

            # create the client (authentication not required for trends)
            twitter = Client()
            
            # get the trending topics
            resp, trending = twitter.trends()
          
        """
        return self.request(self.base_search_url+'/trends.json', "GET")
    
    def trends_current(self, exclude=None):
        """
        Returns the current top 10 trending topics on Twitter. The response 
        ncludes the time of the request, the name of each trending topic,
        and query used on Twitter Search results page for that topic.
        
        Setting exclude parameter to 'hashtags' will remove all hashtags
        from the trends list.
        
        Example::

            # create the client (authentication not required for trends)
            twitter = Client()
            
            # get the current trending topics, no hashtags
            resp, trending = twitter.trends_current(exclude='hashtags')
          
        """
        params = get_params_dict(exclude=exclude)
            
        return self.request(self.base_search_url+'/trends/current.json?%s' %
                             urlencode(params), "GET")
    
    def trends_daily(self, date=None, exclude=None):
        """
        Returns the top 20 trending topics for each hour in a given day.
        
        Setting exclude parameter to 'hashtags' will remove all hashtags
        from the trends list.
        
        Example::

            # create the client (authentication not required for trends)
            twitter = Client()
            
            # get the today's trending topics
            from datetime import date
            resp, trending = twitter.trends_daily(date=date.today())
          
        """
        if isinstance(date, datetype):
            date = date.strftime('%Y-%m-%d')
        params = get_params_dict(date=date, exclude=exclude)
            
        return self.request(self.base_search_url+'/trends/daily.json?%s' %
                             urlencode(params), "GET")
    
    def trends_weekly(self, date=None, exclude=None):
        """
        Returns the top 30 trending topics for each day in a given week.
        
        date parameter specifies a start date for the report.
        
        Setting exclude parameter to 'hashtags' will remove all hashtags
        from the trends list.
        
        Example::

            # create the client (authentication not required for trends)
            twitter = Client()
            
            # get the trending topics for a week
            resp, trending = twitter.trends_weekly()
          
        """
        if isinstance(date, datetype):
            date = date.strftime('%Y-%m-%d')
        params = get_params_dict(date=date, exclude=exclude)
            
        return self.request(self.base_search_url+'/trends/weekly.json?%s' %
                             urlencode(params), "GET")
    
    ###################
    # Timeline Methods
    ###################
    
    def statuses_home_timeline(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns the most recent statuses, including retweets, posted by the
        authenticating user and that user's friends.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/home_timeline.json?%s' % urlencode(params), "GET")
    
    def statuses_friends_timeline(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns the most recent statuses posted by the authenticating user and
        that user's friends.
        
        Note: Retweets will not appear in the friends_timeline for backwards
        compatibility. If you want retweets included use home_timeline.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/friends_timeline.json?%s' % urlencode(params),
                "GET")
    
    def statuses_user_timeline(self, user_id=None, screen_name=None,
                        since_id=None, max_id=None, count=None, page=None):
        """
        Returns the most recent statuses posted from the authenticating user.
        It's also possible to request another user's timeline via the user_id
        or screen_name parameter.
        """
        params = get_params_dict(user_id=user_id, screen_name=screen_name,
                    since_id=since_id, max_id=max_id, count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/user_timeline.json?%s' % urlencode(params), "GET")
    
    def statuses_mentions(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns the most recent mentions (status containing @username) for
        the authenticating user.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/mentions.json?%s' % urlencode(params), "GET")
    
    def statuses_retweeted_by_me(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns the most recent retweets posted by the authenticating user.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/retweeted_by_me.json?%s' % urlencode(params), "GET")
    
    def statuses_retweeted_to_me(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns the most recent retweets posted by the authenticating user's
        friends.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/retweeted_to_me.json?%s' % urlencode(params), "GET")
    
    def statuses_retweeted_of_me(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns the most recent tweets of the authenticated user that have
        been retweeted by others.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+
                '/statuses/retweeted_of_me.json?%s' % urlencode(params), "GET")
    
    #################
    # Status Methods
    #################
    
    def statuses_show(self, id):
        """
        Returns a single status, specified by the id parameter.  The status's
        author will be returned inline.
        """
        return self.request(self.base_api_url+
                '/statuses/show/%s.format' % id, "GET")
    
    
    
    def statuses_update(self, status, in_reply_to_status_id=None, lat=None,
                        long=None, place_id=None, display_coordinates=None):
        """
        Updates the authenticating user's status.
        
        Note: A status update with text identical to the authenticating
        user's current status will be ignored to prevent duplicates.
        """
        params = get_params_dict(status=status,
                                 in_reply_to_status_id=in_reply_to_status_id,
                                 lat=lat, long=long, place_id=place_id,
                                 display_coordinates=display_coordinates)
            
        return self.request(self.base_api_url+'/statuses/update.json', "POST",
                             urlencode(params))
    
    def statuses_destroy(self, id):
        """
        Destroys the status specified by the required ID parameter.  The
        authenticating user must be the author of the specified status.
        """ 
        return self.request(self.base_api_url+'/statuses/destroy/%s.json' % id,
                            "POST")
    
    def statuses_retweet(self, id):
        """
        Retweets a tweet. Requires the id parameter of the tweet you are
        Returns the original tweet with retweet details embedded.
        """ 
        return self.request(self.base_api_url+'/statuses/retweet/%s.json' % id,
                            "POST")
    
    def statuses_retweets(self, id, count=None):
        """
        Returns up to 100 of the first retweets of a given tweet.
        """ 
        params = get_params_dict(count=count)
        
        return self.request(self.base_api_url+'/statuses/retweets/%s.json?%s' %
                            (id, urlencode(params)), "GET")
    
    ###############
    # User Methods
    ###############
    
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
        
        params = get_params_dict(user_id=user_id, screen_name=screen_name)
        
        return self.request(self.base_api_url+'/users/show.json?%s' %
                            urlencode(params), "GET")
    
    def users_lookup(self, user_id=None, screen_name=None):
        """
        Return up to 100 users worth of extended information, specified by
        either ID, screen name, or combination of the two. The author's most
        recent status (if the authenticating user has permission) will be
        returned inline.
        """
        if user_id and not isinstance(user_id, str) and \
                                            not isinstance(user_id, int):
            user_id = ",".join(user_id)
        if screen_name and not isinstance(screen_name, str):
            screen_name = ",".join(screen_name)
        
        params = get_params_dict(user_id=user_id, screen_name=screen_name)
        
        return self.request(self.base_api_url+'/users/lookup.json?%s' %
                            urlencode(params), "GET")
    
    def users_search(self, q, per_page=None, page=None):
        """
        Run a search for users similar to Find People button on Twitter.com;
        the same results returned by people search on Twitter.com will be
        returned by using this API (about being listed in the People Search).
        It is only possible to retrieve the first 1000 matches from this API.
        """
        params = get_params_dict(q=q, per_page=per_page, page=page)
        
        return self.request(self.base_api_url+'/users/search.json?%s' %
                            urlencode(params), "GET")
    
    def users_suggestions(self):
        """
        Access to Twitter's suggested user list.  This returns the list of
        suggested user categories.  The category can be used in the
        users_suggestions_category method to get the users in that category.
        """
        return self.request(self.base_api_url+'/users/suggestions.json', "GET")
    
    def users_suggestions_category(self, slug):
        """
        Access the users in a given category of the Twitter suggested user
        list.
        """
        return self.request(self.base_api_url+'/users/suggestions/%s.json' %
                            slug, "GET")
    
    def statuses_friends(self, user_id=None, screen_name=None, cursor=None):
        """
        Returns a user's friends, each with current status inline. They are
        ordered by the order in which the user followed them, most recently
        followed first, 100 at a time.
        
        Use the cursor option to access older friends. With no user specified,
        request defaults to the authenticated user's friends. It's also
        possible to request another user's friends list via the id,
        screen_name or user_id parameter.
        """
        params = get_params_dict(user_id=user_id, screen_name=screen_name,
                                 cursor=cursor)
        
        return self.request(self.base_api_url+'/statuses/friends.json?%s' %
                            urlencode(params), "GET")
    
    def statuses_followers(self, user_id=None, screen_name=None, cursor=None):
        """
        Returns the authenticating user's followers, each with current status
        inline.  They are ordered by the order in which they followed the user,
        100 at a time.
        
        Use the cursor option to access earlier followers.
        """
        params = get_params_dict(user_id=user_id, screen_name=screen_name,
                                 cursor=cursor)
        
        return self.request(self.base_api_url+'/statuses/followers.json?%s' %
                            urlencode(params), "GET")
    
    ###############
    # List Methods
    ###############
    
    def create_list(self, user, name, mode=None, description=None):
        """
        Creates a new list for the authenticated user.
        
        Accounts are limited to 20 lists.
        """
        params = get_params_dict(name=name, mode=mode,
                                 description=description)
        
        return self.request(self.base_api_url+'/%s/lists.json' % user,
                            "POST", urlencode(params))
    
    def update_list(self, user, id, name=None, mode=None, description=None):
        """
        Updates the specified list.
        """
        params = get_params_dict(name=name, mode=mode,
                                 description=description)
        
        return self.request(self.base_api_url+'/%s/lists/%s.json' %
                            (user, id), "POST", urlencode(params))
    
    def get_lists(self, user, cursor=None):
        """
        List the lists of the specified user.
        
        Private lists will be included if the authenticated users is the same
        as the user who'se lists are being returned.
        """
        params = get_params_dict(cursor=cursor)
        
        return self.request(self.base_api_url+'/%s/lists.json?%s' %
                            (user, urlencode(params)), "GET")
    
    def get_list(self, user, id):
        """
        Show the specified list.
        
        Private lists will only be shown if the authenticated user owns the
        specified list.
        """
        return self.request(self.base_api_url+'/%s/lists/%s.json' %
                            (user, id), "GET")
    
    def delete_list(self, user, id):
        """
        Deletes the specified list. Must be owned by the authenticated user.
        """
        return self.request(self.base_api_url+'/%s/lists/%s.json' %
                            (user, id), "DELETE")
    
    def get_list_statuses(self, user, list_id, since_id=None, max_id=None,
                          per_page=None, page=None):
        """
        Show tweet timeline for members of the specified list.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 per_page=per_page, page=page)
        
        return self.request(self.base_api_url+
                            '/%s/lists/%s/statuses.json' %
                            (user, list_id), "GET")
    
    def get_list_memberships(self, user, cursor=None):
        """
        List the lists the specified user has been added to.
        """
        params = get_params_dict(cursor=cursor)
        
        return self.request(self.base_api_url+
                            '/%s/lists/memberships.json?%s' %
                            (user, urlencode(params)), "GET")
    
    def get_list_subscriptions(self, user, cursor=None):
        """
        List the lists the specified user follows.
        """
        params = get_params_dict(cursor=cursor)
        
        return self.request(self.base_api_url+
                            '/%s/lists/subscriptions.json?%s' %
                            (user, urlencode(params)), "GET")
    
    #######################
    # List Members Methods
    #######################
    
    def get_list_members(self, user, list_id, cursor=None):
        """
        Returns the members of the specified list.
        """
        params = get_params_dict(cursor=cursor)
        
        return self.request(self.base_api_url+
                            '/%s/%s/members.json?%s' %
                            (user, list_id, urlencode(params)), "GET")
    
    def add_list_member(self, user, list_id, id):
        """
        Add a member to a list.
        
        id is the user's user_id or screen_name to add.
        
        The authenticated user must own the list to be able to add members to
        it. Lists are limited to having 500 members.
        """
        params = get_params_dict(id=id)
        
        return self.request(self.base_api_url+'/%s/%s/members.json' %
                            (user, list_id), "POST", urlencode(params))
    
    def delete_list_member(self, user, list_id, id):
        """
        Removes the specified member from the list.
        
        id is the user's user_id or screen_name to delete from the list.
        
        The authenticated user must be the list's owner to remove members
        from the list.
        """
        params = get_params_dict(id=id)
        
        return self.request(self.base_api_url+'/%s/%s/members.json?%s' %
                            (user, list_id, urlencode(params)), "DELETE")
    
    def get_list_members_id(self, user, list_id, id):
        """
        Check if a user is a member of the specified list.
        
        id is the user_id or screen_name of the user who you want to know
        is a member or not of the specified list.
        """
        return self.request(self.base_api_url+ '/%s/%s/members/%s.json' %
                            (user, list_id, id), "GET")
    
    ###########################
    # List Subscribers Methods
    ###########################
    
    def get_list_subscribers(self, user, list_id, cursor=None):
        """
        Returns the subscribers of the specified list.
        """
        params = get_params_dict(cursor=cursor)
        
        return self.request(self.base_api_url+
                            '/%s/%s/subscribers.json?%s' %
                            (user, list_id, urlencode(params)), "GET")
    
    def subscribe_to_list(self, user, list_id):
        """
        Make the authenticated user follow the specified list.
        """
        return self.request(self.base_api_url+'/%s/%s/subscribers.json' %
                            (user, list_id), "POST")
    
    def unsubscribe_from_list(self, user, list_id):
        """
        Unsubscribes the authenticated user form the specified list.
        """
        return self.request(self.base_api_url+'/%s/%s/subscribers.json' %
                            (user, list_id), "DELETE")
    
    def get_list_subscribers_id(self, user, list_id, id):
        """
        Check if the specified user is a subscriber of the specified list.
        
        id is the user_id or screen_name of the user who you want to know
        is a subscriber or not of the specified list.
        """
        return self.request(self.base_api_url+ '/%s/%s/subscribers/%s.json' %
                            (user, list_id, id), "GET")
    
    #########################
    # Direct Message Methods
    #########################
    
    def direct_messages(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns a list of the most recent direct messages sent to the
        authenticating user. Includes detailed information about the
        sending and recipient users.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+'/direct_messages.json', "GET")
    
    def direct_messages_sent(self, since_id=None, max_id=None, count=None,
                               page=None):
        """
        Returns a list of the most recent direct messages by the
        authenticating user. Includes detailed information about the
        sending and recipient users.
        """
        params = get_params_dict(since_id=since_id, max_id=max_id,
                                 count=count, page=page)
        
        return self.request(self.base_api_url+'/direct_messages/sent.json',
                            "GET")
    
    def direct_messages_new(self, user, text):
        """
        Sends a new direct message to the specified user from the
        authenticating user.
        
        Returns the sent message in the requested format when successful.
        """
        params = get_params_dict(user=user, text=text)
        
        return self.request(self.base_api_url+'/direct_messages/new.json',
                            "POST", urlencode(params))
    
    def direct_messages_destroy(self, id):
        """
        Destroys the direct message specified in the required ID parameter.
        
        The authenticating user must be the recipient of the specified
        direct message.
        """
        return self.request(self.base_api_url+
                            '/direct_messages/destroy/%s.json' % id, "DELETE")
    
    
    #####################
    # Friendship Methods
    #####################
    
    def friendships_create(self, user_id=None, screen_name=None, follow=False):
        """
        Allows the authenticating users to follow the user specified in
        the ID parameter.  Returns the befriended user in the requested
        format when successful.  Returns a string describing the failure
        condition when unsuccessful. If you are already friends with the
        user an HTTP 403 will be returned.
        
        Setting follow to True enables notifications for the target user
        in addition to becoming friends.
        """
        if not user_id and not screen_name:
            raise Exception("A user_id or screen_name must be provided.")
        
        if user_id and screen_name:
            raise Exception("A user_id OR screen_name must be provided.")
        
        if follow:
            follow = 'true'
        params = get_params_dict(user_id=user_id, screen_name=screen_name,
                                 follow=follow)
        
        return self.request(self.base_api_url+'/friendships/create.json',
                            "POST", urlencode(params))

    def friendships_destroy(self, user_id=None, screen_name=None):
        """
        Allows the authenticating users to unfollow the user specified in
        the ID parameter. Returns the unfollowed user in the requested
        format when successful. Returns a string describing the failure
        condition when unsuccessful.
        """
        if not user_id and not screen_name:
            raise Exception("A user_id or screen_name must be provided.")
        
        if user_id and screen_name:
            raise Exception("A user_id OR screen_name must be provided.")
        
        params = get_params_dict(user_id=user_id, screen_name=screen_name)
        
        return self.request(self.base_api_url+'/friendships/destroy.json',
                            "POST", urlencode(params))
    
    def friendships_exists(self, user_a, user_b):
        """
        Tests for the existance of friendship between two users.
        Will return true if user_a follows user_b, otherwise will return false.
        
        user_a and user_b can be the user_id or screen_name of the users.
        """
        params = get_params_dict(user_a=user_a, user_b=user_b)
        
        return self.request(self.base_api_url+'/friendships/exists.json?%s' %
                            urlencode(params), "GET")
    
    #######################
    # Social Graph Methods
    #######################
    def friends_ids(self, user_id=None, screen_name=None, cursor=None):
        """
        Returns an array of numeric IDs for every user the specified user
        is following.
        """
        if not user_id and not screen_name:
            raise Exception("A user_id or screen_name must be provided.")
        
        if user_id and screen_name:
            raise Exception("A user_id OR screen_name must be provided.")
        
        params = get_params_dict(user_id=user_id, screen_name=screen_name,
                                 cursor=cursor)
        
        return self.request(self.base_api_url+'/friends/ids.json?%s' %
                            urlencode(params), "GET")
    
    def followers_ids(self, user_id=None, screen_name=None, cursor=None):
        """
        Returns an array of numeric IDs for every user following the
        specified user.
        """
        if not user_id and not screen_name:
            raise Exception("A user_id or screen_name must be provided.")
        
        if user_id and screen_name:
            raise Exception("A user_id OR screen_name must be provided.")
        
        params = get_params_dict(user_id=user_id, screen_name=screen_name,
                                 cursor=cursor)
        
        return self.request(self.base_api_url+'/followers/ids.json?%s' %
                            urlencode(params), "GET")


def get_params_dict(**kwargs):
    """
    Utility function that returns a dict with the set parameters (not None)
    """
    for key in kwargs.keys():
        if kwargs[key] == None:
            del kwargs[key]
    return kwargs


__all__ = ["OAuth", "BasicAuth", "Client"]



