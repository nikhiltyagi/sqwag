from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import serializers
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.mail.message import BadHeaderError
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from httplib2 import Http
#from instagram.client import InstagramAPI
from oauth.oauth import OAuthToken
from sqwag_api.constants import *
from sqwag_api.forms import *
from sqwag_api.helper import *
from sqwag_api.models import *
from sqwag_api.twitterConnect import *
from time import gmtime, strftime
from urllib import urlencode
import datetime
import httplib
import oauth.oauth as oauth
import random
import settings
import sha
import simplejson
import time
import urlparse
import json
from django.core import serializers
from sqwag_api.elsaticsearch import *
from sqwag_api.InstaService import *
successResponse = {}
successResponse['status'] = SUCCESS_STATUS_CODE
successResponse['message'] = SUCCESS_MSG
failureResponse = {}

def index(request):
    return HttpResponse("Hello, world. You're at the sqwag index.")

def loginUser(request):
    if 'username' in request.POST:
        if 'password' in request.POST:
            uname = request.POST['username']
            pword = request.POST['password']
            try:
                User.objects.get(username=uname)
            except User.DoesNotExist:
                try:
                    usrprf = UserProfile.objects.get(username=uname)
                    uname = usrprf.user.username
                except UserProfile.DoesNotExist:
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = 'invalid username'
                    return failureResponse
            user = authenticate(username=uname, password=pword)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    user = User.objects.get(username=uname)
                    respObj = {}
                    respObj['username'] = user.username
                    respObj['id'] = user.id
                    respObj['first_name'] = user.first_name
                    respObj['last_name'] = user.last_name
                    respObj['email'] =  user.email
                    successResponse['result'] = respObj
                    return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
                else:
                    failureResponse['status'] = ACCOUNT_INACTIVE
                    failureResponse['error'] = "your account is not active"
                    return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
            else:
                failureResponse['status'] = INVALID_CREDENTIALS
                failureResponse['error'] = "invalid credentials"
                return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = INVALID_CREDENTIALS
            failureResponse['error'] = "invalid credentials"
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = INVALID_CREDENTIALS
        failureResponse['error'] = "invalid credentials"
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    
def registerUser(request):
    if request.method == "POST":
        form = RegisterationForm(request.POST)
        if form.is_valid():
            #fname = form.cleaned_data['first_name']
            #lname = form.cleaned_data['last_name']
            pwd = form.cleaned_data['password']
            fullname = form.cleaned_data['username']
            email = form.cleaned_data['email']
            #uname = form.cleaned_data['username']
            user = User.objects.create_user(email, email, pwd)
            #user.first_name = fname
            #user.last_name = lname
            user.date_joined = datetime.datetime.now()
            user.is_active = False
            user.save();
            # create a profile for this user
            usrprof = UserProfile.objects.create(user=user,sqwag_count=0, following_count=0,followed_by_count=0,displayname=fullname,fullname=fullname)
            registration_profile = RegistrationProfile.objects.create_profile(user)
            #current_site = Site.objects.get_current()
            subject = "Activation link from sqwag.com"
            host = request.get_host()
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'
            message = protocol + host + '/sqwag/activate/' + str(user.id) + '/' + registration_profile.activation_key
            mailer = Emailer(subject="Activation link from sqwag.com", body=message, from_email='coordinator@sqwag.com', to=user.email, date_created=time.time())
            mailentry(mailer) 
            reldat= {}
            #this needs to be cronned as part of cron mail
            #send_mail(subject,message,'coordinator@sqwag.com',[user.email],fail_silently=False)
            #subscribe own feeds
            relationShip = Relationship(subscriber=user,producer=user)
            relationShip.date_subscribed = int(time.time())
            relationShip.permission = True
            relationShip.save()
            print relationShip.date_subscribed
            CreateDocument(relationShip,relationShip.id,ELASTIC_SEARCH_RELATIONSHIP_POST)
            userdata = {}
            userdata['user_auth'] = User.objects.get(pk=user.id)
            userdata['user_profile'] = UserProfile.objects.get(user=user)  
#           userdata['user'] = complete_user
            CreateDocument(userdata,user.id,ELASTIC_SEARCH_USER_POST)
            successResponse['result'] = "Activation link is sent to the registration mail"
            #TODO: send email with activation link
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = form.errors
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['error'] = "Not a Post request."
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def requestInvitation(request):
    if request.method == "POST":
        form = RequestInvitationForm(request.POST)
        if form.is_valid():
            reqInvitation = form.save(commit=False)
            reqInvitation.date_requested = time.time()
            reqInvitation.save()
            successResponse['result'] = "success"
            dateCreated = time.time()
            mailer = Emailer(subject=SUBJECT_REQ_INVITE, body=BODY_REQ_INVITE, from_email='coordinator@sqwag.com', to=reqInvitation.email, date_created=dateCreated)
            mailentry(mailer)
            #send_mail(SUBJECT_REQ_INVITE, BODY_REQ_INVITE, 'coordinator@sqwag.com',to, fail_silently=True)
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = form.errors
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        return HttpResponse("not a POST request, please send a POST request")

def cronMail(request):
    emails = Emailer.objects.filter(is_sent=False)
    for email in emails:
        try:
            to_email = []
            to_email.append(email.to)
            send_mail(email.subject, email.body, email.from_email, to_email, fail_silently=False)
            email.is_sent = True
            email.status = "sent"
            email.save()
        except BadHeaderError:
            email.status = "invlaid header found"
            email.save()
        except Exception, e:
            email.status = e.message
            email.save()
    successResponse['result'] = "success"
    return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')

def authTwitter(request):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    twitterConnect = TwitterConnect()
    twitterConnect.GetRequest()
    tokenString = twitterConnect.mOauthRequestToken.to_string()
    request.session[twitterConnect.mOauthRequestToken.key] = tokenString
    request.session.modified = True
    return HttpResponseRedirect(twitterConnect.mOauthRequestUrl)


def accessTweeter(request):
    key = request.GET['oauth_token']
    tokenString = request.session.get(key, False)
    if tokenString:
        pOauthRequestToken = OAuthToken.from_string(tokenString)
        pPin = request.GET['oauth_verifier']
        oauthAccess = OauthAccess(pOauthRequestToken, pPin)
        oauthAccess.getOauthAccess()
        # store mOauthAccessToken in data base for further use.
        # check if an entry already exists in useraccount
        try:
            userAccount = getActiveUserAccount(request.user, ACCOUNT_TWITTER)
            print oauthAccess.mUser.GetId()
            userAccount.account_id = oauthAccess.mUser.GetId()
            userAccount.access_token = oauthAccess.mOauthAccessToken.to_string()
            userAccount.date_created = time.time()
            userAccount.account_data = oauthAccess.mUser.AsJsonString()
            userAccount.account_pic = oauthAccess.mUser.GetProfileImageUrl()
            userAccount.account_handle = oauthAccess.mUser.GetScreenName()
            
        except UserAccount.DoesNotExist:
        # make entry in userAccount table
            userAccount = UserAccount(user=request.user,
                                  account=ACCOUNT_TWITTER,
                                  account_id=oauthAccess.mUser.GetId(),
                                  access_token=oauthAccess.mOauthAccessToken.to_string(),
                                  date_created=time.time(),
                                  account_data=oauthAccess.mUser.AsJsonString(),
                                  account_pic=oauthAccess.mUser.GetProfileImageUrl(),
                                  account_handle=oauthAccess.mUser.GetScreenName(),
                                  is_active=True
                                  )
        try:
            userAccount.full_clean()
            userAccount.save()
            successResponse['result'] = oauthAccess.mUser.AsDict();
            # follow this user by TWITTER_USER
            if request.user.id == settings.SQWAG_USER_ID:
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            sqwagTwitterUserAccount = getActiveUserAccount(settings.SQWAG_USER_ID, ACCOUNT_TWITTER)
            sqAccessTokenString = sqwagTwitterUserAccount.access_token
            sqAccessToken = OAuthToken.from_string(sqAccessTokenString)
            api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                            access_token_key=sqAccessToken.key,
                            access_token_secret=sqAccessToken.secret)
            followedUser = api.CreateFriendship(oauthAccess.mUser.GetId())
            successResponse['followed'] = followedUser.AsDict()
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        except ValidationError, e :
            failureResponse['status'] = SYSTEM_ERROR
            failureResponse['error'] = "some error occured, please try later" + e.message
            #TODO: log it
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = SYSTEM_ERROR
        failureResponse['error'] = "some error occured, please try later"#rc.FORBIDDEN
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def logoutUser(request):
    if request.user.is_authenticated():
        logout(request)
        successResponse['result'] = "success"
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['error'] = "Not a valid user" 
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    
def activateUser(request, id, key):
    user = User.objects.get(pk=id)
    if not user.is_active:
        Reg_prof = RegistrationProfile.objects.get(user=id, activation_key=key)
        if Reg_prof:
            #user = User.objects.get(pk=id)
            user.is_active = True
            user.save()
            Reg_prof.date_activated = time.time()
            Reg_prof.is_deleted = True
            Reg_prof.save()
            respObj = {}
            respObj['message'] = "Account is Activated"
            respObj['username'] = user.username
            respObj['id'] = user.id
            respObj['first_name'] = user.first_name
            respObj['last_name'] = user.last_name
            respObj['email'] = user.email
            successResponse['result'] = respObj
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = 'FAILED'
            failureResponse['error'] = 'Activation key not valid'
    else:
        respObj = {}
        respObj['message'] = "Your Account is already active" 
        respObj['username'] = user.username
        respObj['id'] = user.id
        respObj['first_name'] = user.first_name
        respObj['last_name'] = user.last_name
        respObj['email'] = user.email
        successResponse['result'] = respObj
        #TODO: send email with activation link
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            
def syncTwitterFeeds(request):
    sqwagTwitterUserAccount = getActiveUserAccount(settings.SQWAG_USER_ID, ACCOUNT_TWITTER)
    sqAccessTokenString = sqwagTwitterUserAccount.access_token
    sqAccessToken = OAuthToken.from_string(sqAccessTokenString)
    api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                    consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                    access_token_key=sqAccessToken.key,
                    access_token_secret=sqAccessToken.secret)
    #check in db what was the last tweet's id fetched
    feeds = None
    try:
        syncTwitterFeed = SyncTwitterFeed.objects.all().order_by('-last_sync_time')[0]
        last_tweet = syncTwitterFeed.last_tweet
        if (time.time() - syncTwitterFeed.last_sync_time > 10):
            feeds = api.GetFriendsTimeline(user=None, since_id=last_tweet)
        else:
            failureResponse['status'] = TO_MANY_REQUESTS
            failureResponse['error'] = 'Too many requests in too less a time interval'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    except:
        feeds = api.GetFriendsTimeline(user=None)
    if(feeds):
        for feed in reversed(feeds):
            twitterUser = feed.GetUser()
            try:
                userAccount = UserAccount.objects.get(account_id=twitterUser.GetId(), account='twitter', is_active=True)
                #check if square exists for this feed
                try:
                    sqwagUser = userAccount.user
                    Square.objects.get(user=sqwagUser, content_id=feed.GetId())
                except Square.DoesNotExist:
                    # now create a square of this tweet by this sqwag user
                    square = Square(user=sqwagUser, content_type='tweet', content_src='twitter.com', content_id=feed.GetId(),
                                    content_data=feed.GetText(), date_created=feed.GetCreatedAtInSeconds(),
                                    shared_count=0)
                    square.user_account = userAccount
                    try:
                        square.full_clean(exclude='content_description')
                        square.save()
                        saveSquareBoilerPlate(request=request,user=square.user, square=square, date_created=square.date_created)
                    except ValidationError:
                        print  "error in saving square"# TODO: log this
            except UserAccount.DoesNotExist:
                print "user account does not exist"
        lastFeed = feeds[0]
        syncTwitterFeed = SyncTwitterFeed(last_tweet=lastFeed.GetId(), date_created=feed.GetCreatedAtInSeconds(),
                                          last_sync_time=time.time())
        try:
            syncTwitterFeed.full_clean()
            syncTwitterFeed.save()
        except ValidationError, e:
            print "error in saving syncTwitterFeed"
        successResponse['result'] = 'success'
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = NOT_FOUND
        failureResponse['error'] = 'no new feeds found'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def retweet(request, square_id):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = getActiveUserAccount(request.user, ACCOUNT_TWITTER)
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        square = Square.objects.get(pk=square_id)
        tweet = long(square.content_id)
        status = api.RetweetPost(tweet)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        #else:
            #failureResponse['result'] = "BAD REQUEST"
            #return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript') 
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['error'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def replyTweet(request, square_id, message, user_handle):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = getActiveUserAccount(request.user, ACCOUNT_TWITTER)
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        #if isinstance( tweetId, long ):
        square = Square.objects.get(pk=square_id)
        tweet = long(square.content_id)
        status = api.PostUpdate('@' + user_handle + ' ' + message, tweet)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['error'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def postTweet(request, message):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = getActiveUserAccount(getActiveUserAccount, 'twitter')
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        #if isinstance( tweetId, long ):
        status = api.PostUpdate(message)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['error'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    
def favTweet(request, square_id):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = getActiveUserAccount(request.user, 'twitter')
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        #if isinstance( tweetId, long ):
        square = Square.objects.get(pk=square_id)
        status = api.GetStatus(square.content_id)
        fav = api.CreateFavorite(status)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['error'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def authInsta(request):
    # get authttoken
    authorizationUrl = settings.INSTA_AUTHORIZE_URL + 'client_id=' + settings.INSTA_CLIENT_ID + '&redirect_uri=' + settings.INSTA_CALLBACK_URL + '&response_type=code'
    return HttpResponseRedirect(authorizationUrl)

def accessInsta(request):
    if 'code' in request.GET:
        codeReceived = request.GET['code']
        
        h = Http()
        data = dict(client_id=settings.INSTA_CLIENT_ID, client_secret=settings.INSTA_CLIENT_SECRET,
                    grant_type='authorization_code', redirect_uri=settings.INSTA_CALLBACK_URL,
                    code=codeReceived)
        resp, content = h.request(settings.INSTA_ACCESS_TOKEN_URL, "POST", urlencode(data))
        #print resp
        #respJson = json.loads(resp)
        if resp.status == 200:
            contentJson = simplejson.loads(content)
            try:
                print "check is insta account already exists for this user"
                userAccount = getActiveUserAccount(request.user, ACCOUNT_INSTAGRAM)
                print "insta account already present, update account info"
                userAccount.access_token = contentJson['access_token']
                userAccount.date_created=time.time()
                userAccount.account_data=content
                userAccount.account_pic=contentJson['user']['profile_picture']
                userAccount.account_handle=contentJson['user']['username']
                userAccount.is_active=True
            except UserAccount.DoesNotExist:
                print "insta account does not exist, creating fresh account"
                userAccount = UserAccount(user=request.user, account=ACCOUNT_INSTAGRAM, account_id=contentJson['user']['id'],
                                          access_token=contentJson['access_token'], date_created=time.time(),
                                          account_data=content, account_pic=contentJson['user']['profile_picture'],
                                          account_handle=contentJson['user']['username'], is_active=True, last_object_id=1)
            try:
                userAccount.full_clean()
                print "saving account details"
                userAccount.save()
                print "returning"
                successResponse['result'] = contentJson;
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            except ValidationError, e:
                failureResponse['status'] = SYSTEM_ERROR
                failureResponse['error'] = "some error occured :(, please try later" + e.message
                #TODO: log it
                return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = resp.status
            failureResponse['error'] = 'INSTA ERROR'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['error'] = 'GET parameter missing'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def getInstaFeed(request):
    instaUserAccount = getActiveUserAccount(request.user, ACCOUNT_INSTAGRAM)
    url = "https://api.instagram.com/v1/users/self/feed?access_token=" + instaUserAccount.access_token
    h = Http()
    resp, content = h.request(url, "GET")
    if resp.status == 200:
        contentJson = simplejson.loads(content)
        return HttpResponse(content, mimetype='application/javascript') 
    #successResponse['result']=media
    #return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
def forgotPwd(request):
    form = forgotPwdForm(request.POST)
    if form.is_valid():
        user = form.cleaned_data['username']
        user_obj = User.objects.get(username=user)
        if user_obj:
            user_prof = UserProfile.objects.get(user=user_obj)
            activation_key = user_prof.create_reset_key(user_prof)
            user_prof.pwd_reset_key = activation_key
            user_prof.save()
            #subject = "pwd reset link from sqwag.com"
            host = request.get_host()
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'
            message = protocol + host + '/sqwag/pwdreset/' + str(user_obj.id) + '/' + activation_key
            mailer = Emailer(subject="Activation link from sqwag.com",body=message,from_email='coordinator@sqwag.com',to=user_obj.email,date_created=time.time())
            mailentry(mailer)
            successResponse['result'] = 'mail sent successfully' 
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['result'] = NOT_FOUND
            failureResponse['message'] = 'invalid username'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def forgotPwdKey(request, id, key):
    userProf = UserProfile.objects.get(user=id, pwd_reset_key=key)
    #TODO change http response to rendertoresponse
    if userProf:
        successResponse['result'] = 'you can change your pwd'
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    else:
        failureResponse['result'] = BAD_REQUEST
        failureResponse['error'] = 'username and activation key does not match'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
def newPwd(request):
    form = PwdResetForm(request.POST)
    if form.is_valid():
        pwd = request.POST['password']
        user_id = request.POST['id']
        user_obj = User.objects.get(pk=user_id)
        user_obj.set_password(pwd)
        user_obj.save()
        successResponse['result'] = 'password changes successfully'
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    else:
        failureResponse['result'] = BAD_REQUEST
        failureResponse['error'] = 'invalid form'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def editEmail(request):
    form = EditEmailForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        oldpwd = form.cleaned_data['oldPassword']
        user = request.user
        if(user.check_password(oldpwd)):
            if email:
                user.email = email
                user.save()
                successResponse['result'] = 'email changed successfully'
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            else:
                failureResponse['result'] = BAD_REQUEST
                failureResponse['error'] = 'blank email'
                return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        else:
            failureResponse['result'] = BAD_REQUEST
            failureResponse['error'] = 'password does not match'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')    

    else:
        failureResponse['result'] = BAD_REQUEST
        failureResponse['error'] = form.errors
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def editDisplayName(request):
    form = EditDisplayName(request.POST)
    if form.is_valid():
        user = request.user
        displayname = form.cleaned_data['displayName']
        if displayname:
            user.displayname = displayname
            user.save()
            successResponse['result'] = 'dislay name changed successfully'
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['result'] = BAD_REQUEST
            failureResponse['error'] = 'blank display name'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['result'] = BAD_REQUEST
        failureResponse['error'] = form.errors
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        
def changePassword(request):
    form = ChangePasswordForm(request.POST)
    if form.is_valid():
        user = request.user
        oldpwd = form.cleaned_data['oldPassword']
        newpwd = form.cleaned_data['newPassword']
        if(user.check_password(oldpwd)):
            user.set_password(newpwd)
            user.save()
            successResponse['result'] = 'password changed successfully'
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['result'] = BAD_REQUEST
            failureResponse['error'] = 'old password does not match'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['result'] = BAD_REQUEST
        failureResponse['error'] = form.errors
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    
def changeUserName(request):
    form = ChangeUserNameForm(request.POST)
    if form.is_valid():
        user = User.objects.get(pk=45)
        pwd = form.cleaned_data['password']
        if(user.check_password(pwd)):
            username = form.cleaned_data['username']
            user.username = username
            user.save()
            successResponse['result'] = 'username changed successfully'
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
            failureResponse['result'] = BAD_REQUEST
            failureResponse['error'] = 'password does not match'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['result'] = BAD_REQUEST
        failureResponse['error'] = form.errors
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
            
def authFacebook(request):
    authorizationUrl = settings.FACEBOOK_AUTHORIZE_URL+'client_id='+settings.FACEBOOK_APP_ID+'&redirect_uri='+settings.FACEBOOK_CALLBACK_URL+'&response_type=code'
    return HttpResponseRedirect(authorizationUrl)

def accessFacebook(request):
    if 'code' in request.GET:
        codeReceived = request.GET['code']       
        h = Http()
        data = dict(client_id=settings.FACEBOOK_APP_ID, client_secret=settings.FACEBOOK_APP_SECRET,
                    grant_type='authorization_code',redirect_uri=settings.FACEBOOK_CALLBACK_URL,
                    code=codeReceived)
        resp, content = h.request(settings.FACEBOOK_ACCESS_TOKEN_URL, "POST", urlencode(data))
        print resp
        accesstoken = dict(urlparse.parse_qsl(content)).get('access_token')
        #respJson = json.loads(resp)
        if resp.status==200:
            userinfo = h.request('https://graph.facebook.com/me?access_token='+accesstoken,"GET")
            #print userinfo
            #print userinfo[1]
            #print userinfo[0]['status']
            userinformation = json.loads(userinfo[1])
            #print userinformation['username']
            #contentJson = json.dumps(userinfo)
            userPic = h.request('https://graph.facebook.com/'+userinformation['username']+'/picture?type=small')
            #print userPic[0]
            #print userinformation['email']
            userPicture = userPic[0]
            userAccount = UserAccount(user=request.user,account=ACCOUNT_FACEBOOK, account_id=userinformation['id'],
                                      access_token=accesstoken, date_created=time.time(),
                                      account_data=userinfo,account_pic=userPicture['content-location'],
                                      account_handle=userinformation['username'],is_active=True)
            try:
                userAccount.full_clean()
                userAccount.save()
                successResponse['result'] = userinfo;
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            except ValidationError, e:
                failureResponse['status'] = SYSTEM_ERROR
                failureResponse['error'] = "some error occured, please try later"+e.message
                #TODO: log it
                return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = resp.status
            failureResponse['message'] = 'facebook ERROR'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['message'] = 'GET parameter missing'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    
def authFacebookNewUser(request):
    authorizationUrl = settings.FACEBOOK_AUTHORIZE_URL+'client_id='+settings.FACEBOOK_APP_ID+'&redirect_uri='+settings.FACEBOOK_CALLBACK_URL_NEW_USER+'&response_type=code&scope=email'
    return HttpResponseRedirect(authorizationUrl)

def accessFacebookNewUser(request):
    if 'code' in request.GET:
        codeReceived = request.GET['code']       
        h = Http()
        data = dict(client_id=settings.FACEBOOK_APP_ID, client_secret=settings.FACEBOOK_APP_SECRET,
                    grant_type='authorization_code',redirect_uri=settings.FACEBOOK_CALLBACK_URL_NEW_USER,
                    code=codeReceived)
        resp, content = h.request(settings.FACEBOOK_ACCESS_TOKEN_URL, "POST", urlencode(data))
        print resp
        accesstoken = dict(urlparse.parse_qsl(content)).get('access_token')
        #respJson = json.loads(resp)
        if resp.status==200:
            userinfo = h.request('https://graph.facebook.com/me?access_token='+accesstoken,"GET")
            #print userinfo[1]
            #print userinfo[0]['status']
            userinformation = json.loads(userinfo[1])
            #print userinformation['username']
            #contentJson = json.dumps(userinfo)
            userPic = h.request('https://graph.facebook.com/'+userinformation['username']+'/picture?type=small')
            #print userPic[0]
            userPicture = userPic[0]
            user = User(username=userinformation['email'],email=userinformation['email'],first_name=userinformation['first_name'],
                        last_name=userinformation['last_name'],is_active=True,)
            user.date_joined = datetime.datetime.now()
            user.save()
            usrprof = UserProfile(user=user,sqwag_image_url=userPicture['content-location'],sqwag_cover_image_url=userPicture['content-location'],sqwag_count=0, following_count=0,followed_by_count=0)
            usrprof.save()
            usrprof.displayname = userinformation['name']
            usrprof.fullname = userinformation['name']
            usrprof.save()
            userAccount = UserAccount(user=user,account=ACCOUNT_FACEBOOK, account_id=userinformation['id'],
                                      access_token=accesstoken, date_created=time.time(),
                                      account_data=userinfo,account_pic=userPicture['content-location'],
                                      account_handle=userinformation['username'],is_active=True)
            try:
                userAccount.full_clean()
                userAccount.save()
                successResponse['result'] = userinfo;
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            except ValidationError, e:
                failureResponse['status'] = SYSTEM_ERROR
                failureResponse['error'] = "some error occured, please try later"+e.message
                #TODO: log it
                return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = resp.status
            failureResponse['message'] = 'facebook ERROR'
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['message'] = 'GET parameter missing'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')   
    
def GetElasticSearch(request):
    import jsonpickle
    result = GetDocument()
    for r in result:
        print r
    return HttpResponse(jsonpickle.encode(r,unpicklable=False),mimetype='application/javascript')

def instaSubsCallback(request):
    if request.method == "GET":
        if 'hub.mode' in request.GET and 'hub.challenge' in request.GET and 'hub.verify_token' in request.GET:
            #get the challenge
            challenge = request.GET['hub.challenge']
            return HttpResponse(challenge,mimetype='application/javascript')
        else:
            failureResponse['result'] = SYSTEM_ERROR
            failureResponse['error'] = "some error at instagram server"
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    elif request.method == "POST":
        print "inside insta call back post"
        resp = request.raw_post_data
        print "resp received is :" + resp
        mailer = Emailer(subject="insta realtime feed", body=resp, from_email='coordinator@sqwag.com', to='vaibps17@gmail.com', date_created=time.time())
        mailentry(mailer)
        print "mailer entry done"
        print "decoding resp"
        respArrayObj = jsonpickle.decode(resp)
        for respObj in respArrayObj:
            print respObj['object_id']
            print "syncing feeds for "+ respObj['object_id']
            syncInstaFeed(insta_user_id=respObj['object_id'])
            print "done syncing feeds for "+ respObj['object_id']
        print "sync insta feed done"
        return HttpResponse('thankyou!',mimetype='application/javascript')

def createInstaSubscription(request):
    h = Http()
    data = dict(client_id=settings.INSTA_CLIENT_ID,client_secret=settings.INSTA_CLIENT_SECRET,object='user',aspect='media',
                    callback_url=settings.INSTA_SUBS_CALLBACK_URL,
                    verify_token='sqwagbetauser')
    resp, content = h.request(settings.INSTA_SUBSCRIPTION_URL, "POST", urlencode(data))
    if resp.status == 200:
        print "resp.status is 200, printing content"
    return HttpResponse(content, mimetype='application/javascript')

def test(request):
    fields = ["user_auth.username","user_auth.email"]
    query = {}
    term = {}
    term['user_auth.username'] = "nikhil1231"
    query['term'] = term
    r = GetDocument(fields,query,ELASTIC_SEARCH_USER_GET)

def pocInsta(request):
    x = syncInstaFeed(insta_user_id=8314228)
    #x= getUserRecentFeed(count=10, min_id=40, access_token='52192801.6e7b6c7.d45ef561f92b414f8e0c9630220b3c09', user_id=52192801);
    return HttpResponse(x, mimetype='application/javascript')
