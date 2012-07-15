'''
Created on 15-Jul-2012

@author: saini
'''
from sqwag_api.constants import *
from httplib2 import Http
import jsonpickle

def getUserRecentFeed(count=10, max_timestamp=None, access_token=None,
                      min_timestamp=None, min_id=2, max_id=None, user_id=None):
    '''
https://api.instagram.com/v1/users/3/media/recent/?access_token=52192801.f59def8.030649fc930f4525bf432a93168eef60
Get the most recent media published by a user.
PARAMETERS
COUNT    Count of media to return.
MAX_TIMESTAMP    Return media before this UNIX timestamp.
ACCESS_TOKEN    A valid access token.
MIN_TIMESTAMP    Return media after this UNIX timestamp.
MIN_ID    Return media later than this min_id.
MAX_ID    Return media earlier than this max_id.
'''
    if access_token is not None and user_id is not None:
        url = INSTAGRAM_USER_API_URL+str(user_id)+"/media/recent/?access_token="+access_token
        url_params = ""
        if count:
            url_params +="&COUNT="+str(count)
        if max_timestamp:
            url_params +="&MAX_TIMESTAMP="+str(max_timestamp)
        if min_timestamp:
            url_params +="&MIN_TIMESTAMP="+str(min_timestamp)
        if min_id:
            url_params +="&MIN_ID="+str(min_id)
        if max_id:
            url_params +="&MIN_ID="+str(max_id)
        url +=url_params
        # the url is ready
        print "url for insta feed is : "+url
        # get the feed from insta
        content = getData(url)
        #return content
        return jsonpickle.decode(content)
    else:
        return None

def getData(url=None):
    if url is not None:
        h = Http()
        resp, content = h.request(url, "GET")
        if resp.status == 200:
            print "awesome move ahead"
            print "content is : "+ content
            return content
        else:
            print "damn"+ str(resp.status)
    else:
        return None

def getRequiredInformation(object=None):
    '''
    created_time, link,caption.text, 
    '''
    if object is not None:
        pass
    else:
        return None
