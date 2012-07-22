'''
Created on 21-Apr-2012

@author: saini
'''
SUCCESS_STATUS_CODE = 1
SUCCESS_MSG = "success"

# failure codes
BAD_REQUEST = 400
SYSTEM_ERROR = 500
AUTHENTICATION_ERROR = 401
NOT_FOUND = 404
ACCOUNT_INACTIVE = 410
INVALID_CREDENTIALS = 411
DUPLICATE = 412
NUMBER_OF_SQUARES = 16
TO_MANY_REQUESTS = 3
TWITTER_ACCOUNT_NOT_CONNECTED = 4

# request invitation constants
SUBJECT_REQ_INVITE = "Thankyou for your interest"
BODY_REQ_INVITE = "We have received your request, Thanks for showing your interest in Sqwag"

SUBJECT_SQUARE_ACTION_SHARED = "A user shared your square"
BODY_SQUARE_ACTION_SHARED = "asdasdasdasd"

SUBJECT_SUBSCRIBED = "Your sqwags have been subscribed"
BODY_SUBSCRIBED = "A user has subscribed for you feeds."

#Accounts
ACCOUNT_TWITTER = "twitter"
ACCOUNT_INSTAGRAM = "instagram"
ACCOUNT_FACEBOOK = "facebook"

#Elastic Search
ELASTIC_SEARCH_USER_POST = "http://localhost:9200/sqwag/user/"
ELASTIC_SEARCH_USER_GET = "http://localhost:9200/sqwag/user/_search?"
ELASTIC_SEARCH_RELATIONSHIP_POST = "http://localhost:9200/sqwag/relationship/"
ELASTIC_SEARCH_RELATIONSHIP_GET = "http://localhost:9200/sqwag/relationship/_search?"
ELASTIC_SEARCH_SQUARE_POST = "http://localhost:9200/sqwag/square/"
ELATIC_SEARCH_SQUARE_GET = "http://localhost:9200/sqwag/square/_search?"
ELASTIC_SEARCH_USERSQUARE_POST = "http://localhost:9200/sqwag/usersquare/"
ELASTIC_SEARCH_USERSQUARE_GET = "http://localhost:9200/sqwag/usersquare/_search?"


#INSTAGRAM URLS
INSTAGRAM_HOST_URL = "https://api.instagram.com/v1/"
INSTAGRAM_USER_API_URL = INSTAGRAM_HOST_URL+"users/"



