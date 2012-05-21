from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, \
    ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from piston.handler import BaseHandler
from piston.utils import rc, throttle, validate
from sqwag_api.constants import *
from sqwag_api.forms import CreateSquareForm, CreateRelationshipForm
from sqwag_api.helper import mailentry, handle_uploaded_file
from sqwag_api.models import *
import simplejson
import time

successResponse = {}
successResponse['status'] = SUCCESS_STATUS_CODE
successResponse['message'] = SUCCESS_MSG
failureResponse = {}

class SquareHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE','POST')
    fields = ('id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',('user', ('id','first_name','last_name','email','username',)),(
              'user_account',('id','account_id','date_created','account_pic','account_handle','account')))
    #exclude = ('id', re.compile(r'^private_'))
    model = Square
    def create(self, request, *args, **kwargs):
        '''
        api to create square.
        '''
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        squareForm =  CreateSquareForm(request.POST)
        if squareForm.is_valid():
            square = squareForm.save(commit=False)
            square.date_created = time.time()
            square.shared_count=0
            square.liked_count=0
            square.user = request.user
            if square.content_src == 'twitter.com':
                try:
                    userAccount = UserAccount.objects.filter(user=request.user,account='twitter.com')
                    square.user_account = userAccount
                except UserAccount.DoesNotExist:
                    print "user account does not exist"
            square.save()
            try:
                userProfile = UserProfile.objects.get(user=square.user)
                userProfile.sqwag_count += 1
                userProfile.save()
            except ObjectDoesNotExist:
                print "profile doesnot exist"
            if square:
                successResponse['result'] = square
                return successResponse
            else:
                failureResponse['status'] = SYSTEM_ERROR
                failureResponse['error'] = "System Error."
                return failureResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = squareForm.errors
            return failureResponse

    def read(self, request,id, *args, **kwargs):
        if not self.has_model():
            failureResponse['status'] = SYSTEM_ERROR
            failureResponse['error'] = "System Error."
            return failureResponse 
        try:
            square = Square.objects.get(pk=id)
            successResponse['result'] = square
            return successResponse
        except ObjectDoesNotExist:
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "Not Found"
            return failureResponse
        except MultipleObjectsReturned: # should never happen, since we're using a PK
            failureResponse['status'] = SYSTEM_ERROR
            failureResponse['error'] = "System Error."
            return failureResponse


class ImageSquareHandler(BaseHandler):
    allowed_methods = ('POST')
    fields = ('id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',('user', ('id','first_name','last_name','email','username',)),(
              'user_account',('id','account_id','date_created','account_pic','account_handle','account')))
    model = Square
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"
            return failureResponse
        if request.method == 'POST':
            form = CreateSquareForm(request.POST, request.FILES)
            if form.is_valid():
                if 'content_file' in request.FILES:
                    image_url = handle_uploaded_file(request.FILES['content_file'],request)
                    print type(image_url)
                    square = form.save(commit=False)
                    square.content_type = "image"
                    square.content_data = image_url
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
                        return successResponse
                    else:
                        failureResponse['status'] = SYSTEM_ERROR
                        failureResponse['error'] = "System Error."
                        return failureResponse
                else:
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = "please select an image to upload"
                    return failureResponse
            else:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = form.errors
                return failureResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['message'] = 'POST expected'
            return failureResponse


class UserSelfFeedsHandler(BaseHandler):
    methods_allowed = ('GET',)
    def read(self, request, page):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse 
        squares_all = Square.objects.filter(user=request.user).order_by('-date_created')
        paginator = Paginator(squares_all,NUMBER_OF_SQUARES)
        try:
            squares = paginator.page(page)
        except PageNotAnInteger:
        # If page is not an integer, deliver first page.
            squares = paginator.page(1)
        except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
            squares = paginator.page(paginator.num_pages)
        if squares:
            next_page = int(page) + 1
            #TODO: see if next page exists or not
            next_url = "/user/feeds/"+ str(next_page)
            successResponse['result'] = squares.object_list
            successResponse['nexturl'] = next_url
            return successResponse
        else:
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "Not Found"
        return failureResponse

class ShareSquareHandler(BaseHandler):
    methods_allowed = ('GET','POST',)
    
    def create(self,request, *args, **kwargs):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        if 'square_id' in request.POST:
            if request.POST['square_id'].isdigit():
                squareObj = Square.objects.get(pk=request.POST['square_id'])
                userObj = request.user
                if(squareObj.user==userObj):
                    failureResponse['status'] = DUPLICATE
                    failureResponse['error'] = "you can not share your own square"
                    return failureResponse
                userSquare = UserSquare(user=userObj, square =squareObj,date_shared=time.time()) 
                userSquare.save()
                squareObj.shared_count = squareObj.shared_count + 1
                squareObj.save()
                to_email = squareObj.user.email
                squareObj.id = None
                #saving copy of this square
                if 'description' in request.POST:
                    squareObj.content_description = request.POST['description']
                    squareObj.user = userObj
                    squareObj.shared_count = 0
                    squareObj.liked_count = 0
                    squareObj.date_created = time.time()
                try:
                    squareObj.full_clean(exclude='content_description')
                    squareObj.save()
                    # inform the owner 
                    mailer = Emailer(subject=SUBJECT_SQUARE_ACTION_SHARED,body=BODY_SQUARE_ACTION_SHARED,from_email='coordinator@sqwag.com',to=to_email,date_created=time.time())
                    mailentry(mailer)
                    userProfile = UserProfile.objects.get(user=squareObj.user)
                    userProfile.sqwag_count += 1
                    userProfile.save()
                    successResponse['result'] = squareObj
                    return successResponse
                except ValidationError, e :
                    squareObj = Square.objects.get(pk=request.POST['square_id'])
                    squareObj.shared_count = squareObj.shared_count - 1
                    squareObj.save()
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = "bad entery detected"
                    return failureResponse
                    dummy = e.message() #TODO log error
            else:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = "square_id should be an integer"
                return failureResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "square_id is required"
            return failureResponse

class RelationshipHandler(BaseHandler):
    methods_allowed = ('GET','POST',)
    fields = ('id','date_subscribed','permission',('subscriber', ('id','first_name','last_name','email','username',)),
              ('producer', ('id','first_name','last_name','email','username',)))
    def create(self, request, *args, **kwargs):
        relationshipForm = CreateRelationshipForm(request.POST)
        #relationshipForm.user = request.user
        if relationshipForm.is_valid():
            sub = relationshipForm.cleaned_data['subscriber']
            prod = relationshipForm.cleaned_data['producer']
            # check is subscriber == producer
            if sub == prod:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = "You can not subscribe to yourself :)"
                return failureResponse
            # check if already following
            try:
                rel = Relationship.objects.get(subscriber=sub, producer=prod)
                failureResponse['status'] = DUPLICATE
                failureResponse['error'] = "You are already following this user"
                return failureResponse
            except Relationship.DoesNotExist:
               # go ahed everything is fine
                relationship = relationshipForm.save(commit=False)
                relationship.date_subscribed = time.time()
                relationship.permission = True
                relationship.save()
                #update producer's profile
                userProfile = UserProfile.objects.get(user=relationship.producer)
                userProfile.followed_by_count += 1 
                userProfile.save()
                #update subscriber's profile
                userProfile = UserProfile.objects.get(user=relationship.subscriber)
                userProfile.following_count += 1 
                userProfile.save()
                
                to_email = relationship.producer.email
                # notify producer user
                mailer = Emailer(subject=SUBJECT_SUBSCRIBED,body=BODY_SUBSCRIBED,from_email='coordinator@sqwag.com',to=to_email,date_created=time.time())
                mailentry(mailer)
                successResponse['result'] = relationship
                return successResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = relationshipForm.errors
            return failureResponse

class HomePageFeedHandler(BaseHandler):
    methods_allowed = ('GET',)
    
    def read(self, request, page=1, *args, **kwargs):
        # only authenticated user can get it's own feed
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        user = request.user
        relationships = Relationship.objects.filter(subscriber=user)
        producers =  [relationship.producer for relationship in relationships]
        squares_all = Square.objects.filter(user__in=producers).order_by('-date_created')
        paginator = Paginator(squares_all,NUMBER_OF_SQUARES)
        try:
            squares = paginator.page(page)
            if squares:
                next_page = int(page) + 1
                next_url = "/user/feeds/"+ str(next_page)
                successResponse['result'] = squares.object_list
                successResponse['nexturl'] = next_url
                return successResponse
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "You need to subscribe to receive feeds"
            return failureResponse
        except PageNotAnInteger:
        # If page is not an integer, deliver failure response.
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "page should be an integer"
        except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "page is out of bounds"
        return failureResponse

class DeleteSquareHandler(BaseHandler):
    methods_allowed = ('POST')
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        if "square_id" in request.POST:
            sq_id = request.POST['square_id']
            sq_obj = Square.objects.get(pk=sq_id, user = request.user)
            if sq_obj:
                userProfile = UserProfile.objects.get(user=sq_obj.user)
                userProfile.sqwag_count = userProfile.sqwag_count - 1
                userProfile.save()
                sq_obj.delete()
                successResponse['result'] = "square deleted"
                return successResponse
            else:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = "You are not authorised to delete this square or the square is not present with us.    "
                return failureResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "square_id is required"
            return failureResponse

class TopSqwagsFeedsHandler(BaseHandler):
    methods_allowed = ('GET',)
    
    def read(self, request, page=1, *args, **kwargs):
        # only authenticated user can get it's own feed
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        user = request.user
        relationships = Relationship.objects.filter(subscriber=user)
        producers =  [relationship.producer for relationship in relationships]
        squares_all = Square.objects.filter(user__in=producers).order_by('-liked_count','-shared_count')
        paginator = Paginator(squares_all,NUMBER_OF_SQUARES)
        try:
            squares = paginator.page(page)
            if squares:
                next_page = int(page) + 1
                next_url = "/user/topsqwagsfeeds/"+ str(next_page)
                successResponse['result'] = squares.object_list
                successResponse['nexturl'] = next_url
                return successResponse
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "You need to subscribe to receive feeds"
            return failureResponse
        except PageNotAnInteger:
        # If page is not an integer, deliver failure response.
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "page should be an integer"
        except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "page is out of bounds"
        return failureResponse

class PublicSqwagsFeedsHandler(BaseHandler):
    methods_allowed = ('GET',)
    
    def read(self, request, page=1, *args, **kwargs):
        squares_all = Square.objects.all().order_by('-date_created')
        paginator = Paginator(squares_all,NUMBER_OF_SQUARES)
        try:
            squares = paginator.page(page)
            if squares:
                next_page = int(page) + 1
                next_url = "/user/publicsquaresfeeds/"+ str(next_page)
                successResponse['result'] = squares.object_list
                successResponse['nexturl'] = next_url
                return successResponse
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "Opps no feeds on sqwag platform"
            return failureResponse
        except PageNotAnInteger:
        # If page is not an integer, deliver failure response.
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "page should be an integer"
        except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "page is out of bounds"
        return failureResponse

class UserInfo(BaseHandler):
    methods_allowed = ('GET')
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_data','account_pic','account_handle','account_pic', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count')
    
    def read(self,request,id=None,*args, **kwargs):
        if not id:
            if request.user.is_authenticated():
                id = request.user.id
            else:
                failureResponse['status'] = AUTHENTICATION_ERROR
                failureResponse['error'] = "Login Required"#rc.FORBIDDEN
                return failureResponse
        user_obj = User.objects.get(pk=id)
        userProfile = UserProfile.objects.get(user=user_obj)
        useracc_obj = UserAccount.objects.filter(user=id)
        Respobj = {}
        Respobj['user'] = user_obj
        Respobj['user_profile'] = userProfile
        Respobj['user_accounts']= useracc_obj
        successResponse['result'] = Respobj
        return successResponse
