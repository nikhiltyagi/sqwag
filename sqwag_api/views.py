from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.mail.message import BadHeaderError
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.http import HttpResponse
from sqwag_api.constants import *
from sqwag_api.forms import *
from sqwag_api.helper import *
import datetime
import simplejson
import time
import sha
import random
from sqwag_api.models import *
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

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

def logout(self,request,user_id):
    user_obj = User.objects.get(pk=user_id)
    if user_obj:
        if request.user.is_authenticated():
            logout(request)
            successResponse['result'] = "success"
            return HttpResponse(simplejson.dumps(successResponse), mimetype='application/javascript')
        else:
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
            