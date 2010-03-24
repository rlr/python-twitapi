==============
python-twitapi
==============
:Info: Python client library for the Twitter API.
:Author: Ricky Rosario (http://github.com/rlr)

About
=====
Python-twitapi is a python client library for the Twitter API with full support for
OAuth and Basic Authentication. It is based on python-oauth2 and httplib2.

Installation
============
Fill me in...

Dependencies
============
- httplib2 http://code.google.com/p/httplib2/ ( ``pip install httplib2`` )
- python-oauth2 http://github.com/simplegeo/python-oauth2 ( ``pip install oauth2`` )
- simplejson http://code.google.com/p/simplejson/ ( ``pip install simplejson`` )
  not required for python 2.6+


Examples
========
Search::

    >>> from twitapi import Client
    >>> twitter = Client() # search API doesn't require authentication
    >>> resp, content = twitter.search('python')
    >>> if resp['status'] == '200':
    ...     for tweet in content['results']:
    ...         # do something with the tweet
    ...         pass


Post a tweet - Basic Authentication::

    >>> from twitapi import BasicAuth, Client
    >>> auth = BasicAuth('username', 'password')
    >>> twitter = Client(auth)
    >>> twitter.statuses_update('testing out python-twitapi')

Add a friend - OAuth::

    >>> from twitapi import OAuth, Client
    
    # The very first (one-time) thing we need to do is set up an OAuth application
    # on Twitter at http://twitter.com/oauth_clients. We will get a consumer key and
    # consumer secret for our application.
    >>> CONSUMER_KEY = 'YOUR-CONSUMER-KEY'
    >>> CONSUMER_SECRET = 'YOUR-CONSUMER-SECRET'
    
    # The first step is getting access tokens for a given user, by having them
    # authorize our application.
    >>> auth = OAuth(CONSUMER_KEY, CONSUMER_SECRET)
    >>> request_token = auth.get_request_token()
    >>> auth.get_authorization_url(request_token)
    'http://twitter.com/oauth/authorize?oauth_token=G5rvsVRSSz6g48QQ8pbAKDZNBpgxBM6u81BMeZXBk'
    
    # Next we send the user to the URL above. Once they authorize the application,
    # we can get the access tokens.
    >>> auth.set_token(request_token)
    >>> access_token = auth.get_access_token()
    
    # We usually will want to save this access token in our data store for
    # later use.
    
    # Now we can call the Twitter API on behalf of the user!
    >>> auth.set_token(access_token)
    >>> twitter = Client(auth)
    >>> twitter.friendships_create(screen_name='r1cky')


Twitter API Methods
===================
The following methods are currently implemented::

* search
* trends
* trends_current
* trends_daily
* trends_weekly
* statuses_home_timeline
* statuses_friends_timeline
* statuses_user_timeline
* statuses_mentions
* statuses_retweeted_by_me
* statuses_retweeted_to_me
* statuses_retweeted_of_me
* statuses_update
* users_show
* friendships_create
* friendships_destroy
* friendships_exists

The rest are coming. In the mean time, you can call the request method, passing in
any url (method, body, headers are optional parameters). For example:

    >>> from twitapi import Client
    >>> twitter = Client()
    >>> url = 'http://api.twitter.com/1/account/rate_limit_status.json'
    >>> resp,content = twitter.request(url)
    >>> content
    {'reset_time': 'Tue Mar 23 03:20:55 +0000 2010', 'remaining_hits': 19028,
    'hourly_limit': 20000, 'reset_time_in_seconds': 1269314455}


Or even better, fork and contribute!

Feedback Welcome
================
Please send me any questions and suggestions on how to improve the project!
