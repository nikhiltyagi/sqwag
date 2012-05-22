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
from oauth.oauth import OAuthToken
from sqwag.sqwag_api.constants import *
from sqwag_api.constants import *
from sqwag_api.forms import *
from sqwag_api.helper import *
from sqwag_api.models import *
from sqwag_api.twitterConnect import *
from time import gmtime, strftime
from urllib import urlencode
import datetime
import httplib
import json
import oauth.oauth as oauth
import random
import settings
import sha
import simplejson
import time
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
        form =  RegisterationForm(request.POST)
        if form.is_valid():
            fname = form.cleaned_data['first_name']
            lname = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            pwd = form.cleaned_data['password']
            uname = form.cleaned_data['username']
            user = User.objects.create_user(uname, email, pwd)
            user.first_name = fname
            user.last_name = lname
            user.date_joined = datetime.datetime.now()
            user.is_active = False
            user.save();
            # create a profile for this user
            UserProfile.objects.create(user=user,sqwag_count=0, following_count=0,followed_by_count=0)
            registration_profile = RegistrationProfile.objects.create_profile(user)
            #current_site = Site.objects.get_current()
            subject = "Activation link from sqwag.com"
            host = request.get_host()
            if request.is_secure():
                protocol = 'https://'
            else:
                protocol = 'http://'
            message = protocol + host + '/sqwag/activate/' + str(user.id) + '/' + registration_profile.activation_key
            mailer = Emailer(subject="Activation link from sqwag.com",body=message,from_email='coordinator@sqwag.com',to=user.email,date_created=time.time())
            mailentry(mailer) 
            #this needs to be cronned as part of cron mail
            #send_mail(subject,message,'coordinator@sqwag.com',[user.email],fail_silently=False)
            #subscribe own feeds
            relationShip = Relationship(subscriber=user,producer=user)
            relationShip.date_subscribed = time.time()
            relationShip.permission = True
            relationShip.save()
            
            #respObj['url'] = current_site
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
        form =  RequestInvitationForm(request.POST)
        if form.is_valid():
            reqInvitation = form.save(commit=False)
            reqInvitation.date_requested = time.time()
            reqInvitation.save()
            successResponse['result'] = "success"
            dateCreated = time.time()
            mailer = Emailer(subject=SUBJECT_REQ_INVITE,body=BODY_REQ_INVITE,from_email='coordinator@sqwag.com',to=reqInvitation.email,date_created=dateCreated)
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
            send_mail(email.subject, email.body, email.from_email, to_email,fail_silently=False)
            email.is_sent=True
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
    key =request.GET['oauth_token']
    tokenString = request.session.get(key,False)
    if(tokenString):
        pOauthRequestToken= OAuthToken.from_string(tokenString)
        pPin = request.GET['oauth_verifier']
        oauthAccess = OauthAccess(pOauthRequestToken, pPin)
        oauthAccess.getOauthAccess()
        # store mOauthAccessToken in data base for further use.
        # make entry in userAccount table
        userAccount = UserAccount(user=request.user,account=ACCOUNT_TWITTER, account_id=oauthAccess.mUser.GetId(),
                                  access_token=oauthAccess.mOauthAccessToken.to_string(), date_created=time.time(),
                                  account_data=oauthAccess.mUser.AsJsonString(), account_pic=oauthAccess.mUser.GetProfileImageUrl(),
                                  account_handle=oauthAccess.mUser.GetScreenName())
        try:
            userAccount.full_clean()
            userAccount.save()
            successResponse['result'] = oauthAccess.mUser.AsDict();
            # follow this user by TWITTER_USER
            if request.user.id == settings.SQWAG_USER_ID:
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            sqwagTwitterUserAccount = UserAccount.objects.get(user=settings.SQWAG_USER_ID, account='twitter')
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
            failureResponse['error'] = "some error occured, please try later"+e.message
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
    
def activateUser(request,id,key):
    user = User.objects.get(pk=id)
    if not user.is_active:
        Reg_prof = RegistrationProfile.objects.get(user=id,activation_key=key)
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
            respObj['email'] =  user.email
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
        respObj['email'] =  user.email
        successResponse['result'] = respObj
        #TODO: send email with activation link
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            
def syncTwitterFeeds(request):
    sqwagTwitterUserAccount = UserAccount.objects.get(user=settings.SQWAG_USER_ID, account='twitter')
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
            feeds = api.GetFriendsTimeline(user=None, since_id = last_tweet)
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
                userAccount = UserAccount.objects.get(account_id = twitterUser.GetId(), account='twitter')
                sqwagUser = userAccount.user
                # now create a square of this tweet by this sqwag user
                square = Square(user= sqwagUser, content_type='tweet',  content_src='twitter.com', 
                                content_data = feed.GetText(), date_created = feed.GetCreatedAtInSeconds(),
                                shared_count=0, liked_count=0)
                square.user_account = userAccount
                try:
                    square.full_clean(exclude='content_description')
                    square.save()
                    userProfile = UserProfile.objects.get(user=square.user)
                    userProfile.sqwag_count += 1
                    userProfile.save()
                except ValidationError, e:
                    print  "error in saving square"# TODO: log this
            except UserAccount.DoesNotExist:
                print "user account does not exist"
        lastFeed = feeds[0]
        syncTwitterFeed = SyncTwitterFeed(last_tweet=lastFeed.GetId(),date_created=feed.GetCreatedAtInSeconds(),
                                          last_sync_time=time.time())
        try:
            syncTwitterFeed.full_clean()
            syncTwitterFeed.save()
        except ValidationError, e:
            print "error in saving syncTwitterFeed"
        successResponse['result']= 'success'
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = NOT_FOUND
        failureResponse['message'] = 'no new feeds found'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def retweet(request,tweet_id):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = UserAccount.objects.get(user=request.user, account='twitter')
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        #if isinstance( tweetId, long ):
        tweet = long(tweet_id)
        status = api.RetweetPost(tweet)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        #else:
            #failureResponse['result'] = "BAD REQUEST"
            #return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript') 
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['message'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def replyTweet(request,tweet_id,message,user_handle):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = UserAccount.objects.get(user=request.user, account='twitter')
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        #if isinstance( tweetId, long ):
        tweet = long(tweet_id)
        status = api.PostUpdate('@'+user_handle+' '+message,tweet)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['message'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    
def favTweet(request,tweet_id):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    try:
        userTwitterUserAccount = UserAccount.objects.get(user=request.user, account='twitter')
        userAccessTokenString = userTwitterUserAccount.access_token
        userAccessToken = OAuthToken.from_string(userAccessTokenString)
        api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                        consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                        access_token_key=userAccessToken.key,
                        access_token_secret=userAccessToken.secret)
        #if isinstance( tweetId, long ):
        status = api.GetStatus(tweet_id)
        fav = api.CreateFavorite(status)
        successResponse['result'] = status.AsDict()
        return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
    except UserAccount.DoesNotExist:
        failureResponse['status'] = TWITTER_ACCOUNT_NOT_CONNECTED
        failureResponse['message'] = 'your twitter account in not connected. Please connect twitter'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def uploadImageSquare(request):
    if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    if request.method == 'POST':
        form = CreateSquareForm(request.POST, request.FILES)
        if form.is_valid():
            if 'content_file' in request.FILES:
                image_url = handle_uploaded_file(request.FILES['content_file'],request)
                print type(image_url)
                square = form.save(commit=False)
                square.content_type = "image"
                #square.content_data = image_url
                square.date_created = time.time()
                square.shared_count=0
                square.liked_count=0
                square.user = request.user
                square.save()
                try:
                    userProfile = UserProfile.objects.get(user=square.user)
                    userProfile.sqwag_count += 1
                    userProfile.save()
                except ObjectDoesNotExist:
                    print "profile does not exist"
                if square:
                    successResponse['result'] = square
                    return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
                else:
                    failureResponse['status'] = SYSTEM_ERROR
                    failureResponse['error'] = "System Error."
                    return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
            else:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = "please select an image to upload"
                return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = form.errors
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['message'] = 'POST expected'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')

def authInsta(request):
    # get authttoken
    authorizationUrl = settings.INSTA_AUTHORIZE_URL+'client_id='+settings.INSTA_CLIENT_ID+'&redirect_uri='+settings.INSTA_CALLBACK_URL+'&response_type=code'
    return HttpResponseRedirect(authorizationUrl)
def accessInsta(request):
    if 'code' in request.GET:
        codeReceived = request.GET['code']
        
        h = Http()
        data = dict(client_id=settings.INSTA_CLIENT_ID, client_secret=settings.INSTA_CLIENT_SECRET,
                    grant_type='authorization_code',redirect_uri=settings.INSTA_CALLBACK_URL,
                    code=codeReceived)
        resp, content = h.request(settings.INSTA_ACCESS_TOKEN_URL, "POST", urlencode(data))
        contentJson = json.loads(content)
        userAccount = UserAccount(user=request.user,account=ACCOUNT_INSTAGRAM, account_id=contentJson.user.id,
                                  access_token=contentJson.access_token, date_created=time.time(),
                                  account_data=content, account_pic=contentJson.user.profile_picture,
                                  account_handle=contentJson.user.username)
        try:
            userAccount.full_clean()
            userAccount.save()
            successResponse['result'] = content;
            # follow this user by TWITTER_USER
            if request.user.id == settings.SQWAG_USER_ID:
                return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
            sqwagInstagramUserAccount = UserAccount.objects.get(user=settings.SQWAG_USER_ID, account='instagram')
            sqAccessToken = sqwagInstagramUserAccount.access_token
            #TODO work is remaining. integrate insta live feeds here
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        except ValidationError, e :
            failureResponse['status'] = SYSTEM_ERROR
            failureResponse['error'] = "some error occured, please try later"+e.message
            #TODO: log it
            return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
        successResponse['result'] = content
        return HttpResponse(content, mimetype='application/javascript')
    else:
        failureResponse['status'] = BAD_REQUEST
        failureResponse['message'] = 'GET parameter missing'
        return HttpResponse(simplejson.dumps(failureResponse), mimetype='application/javascript')
