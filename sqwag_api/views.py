from api.handlers import successResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.mail.message import BadHeaderError
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect
from oauth.oauth import OAuthToken
from sqwag_api.constants import *
from sqwag_api.forms import *
from sqwag_api.helper import *
from sqwag_api.models import *
from sqwag_api.twitterConnect import *
from time import gmtime, strftime
import datetime
import httplib
import oauth.oauth as oauth
import settings
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
#            user = form.save(commit=False)
#            user.date_joined = datetime.datetime.now()
#            user.is_active = False
#            user.save();
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
            #subscribe own feeds
            relationShip = Relationship(subscriber=user,producer=user)
            relationShip.date_subscribed = time.time()
            relationShip.permission = True
            relationShip.save()
            respObj = {}
            respObj['username'] = user.username
            respObj['id'] = user.id
            respObj['first_name'] = user.first_name
            respObj['last_name'] = user.last_name
            respObj['email'] =  user.email
            successResponse['result'] = respObj
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
    twitterConnect = TwitterConnect()
    twitterConnect.GetRequest()
    tokenString = twitterConnect.mOauthRequestToken.to_string()
    request.session[twitterConnect.mOauthRequestToken.key] = tokenString
    request.session.modified = True
    return HttpResponseRedirect(twitterConnect.mOauthRequestUrl)

def accessTweeter(request):
    key =request.GET['oauth_token']
    tokenString = request.session.get(key,False)
    pOauthRequestToken= OAuthToken.from_string(tokenString)
    pPin = request.GET['oauth_verifier']
    oauthAccess = OauthAccess(pOauthRequestToken, pPin)
    oauthAccess.getOauthAccess()
    # store mOauthAccessToken in data base for further use.
    
    api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
                            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
                            access_token_key=oauthAccess.mOauthAccessToken.key,
                            access_token_secret=oauthAccess.mOauthAccessToken.secret)
#    api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY,
#                            consumer_secret=settings.TWITTER_CONSUMER_SECRET,
#                            access_token_key=pOauthRequestToken.key,
#                            access_token_secret=pOauthRequestToken.secret)
    successResponse['result'] = oauthAccess.mUser.AsDict();
    return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
