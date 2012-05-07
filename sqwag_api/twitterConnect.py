'''
Created on 05-May-2012

@author: saini
'''
from oauthtwitter import OAuthApi
from sqwag_api import twitter
import settings
class TwitterConnect(object):
    '''
    classdocs
    '''
    CONSUMER_KEY = settings.TWITTER_CONSUMER_KEY
    CONSUMER_SECRET = settings.TWITTER_CONSUMER_SECRET
    AUTHORIZATION_URL = settings.TWITTER_AUTHORIZE_URL
    REQUEST_TOKEN_URL = settings.TWITTER_REQUEST_TOKEN_URL

    def GetRequest(self):
        vOauthApi = OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        self.mOauthRequestToken = vOauthApi.getRequestToken(self.REQUEST_TOKEN_URL)
        self.mOauthRequestUrl = vOauthApi.getAuthorizationURL(self.mOauthRequestToken)

class OauthAccess():
  
    CONSUMER_KEY = settings.TWITTER_CONSUMER_KEY  
    CONSUMER_SECRET = settings.TWITTER_CONSUMER_SECRET  
    ACCESS_TOKEN_URL = settings.TWITTER_ACCESS_TOKEN_URL
  
    mPin = ""
    mOauthRequestToken = ""
    mOauthAccessToken = ""
    mUser = twitter.User
    mTwitterApi = ""
  
    def __init__(self, pOauthRequestToken, pPin):
        self.mOauthRequestToken = pOauthRequestToken
        self.mPin = pPin
  
    def getOauthAccess(self):
        self.mTwitterApi = OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET, self.mOauthRequestToken)
        self.mOauthAccessToken = self.mTwitterApi.getAccessToken(self.mPin)
        self.mAuthenticatedTwitterInstance = OAuthApi(self.CONSUMER_KEY, self.CONSUMER_SECRET, self.mOauthAccessToken)
        self.mUser = self.mAuthenticatedTwitterInstance.GetUserInfo()
#        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
#                            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
#                            access_token_key=self.mOauthAccessToken.key,
#                            access_token_secret=self.mOauthAccessToken.secret)
