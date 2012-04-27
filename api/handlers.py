from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, \
    ValidationError
from piston.handler import BaseHandler
from piston.utils import rc, throttle, validate
from sqwag_api.constants import *
from sqwag_api.forms import CreateSquareForm, CreateRelationshipForm
from sqwag_api.helper import mailentry
from sqwag_api.models import *
import simplejson
import time

successResponse = {}
successResponse['status'] = SUCCESS_STATUS_CODE
successResponse['message'] = SUCCESS_MSG
failureResponse = {}

class SquareHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE','POST')
    fields = ('id','content_src','content_type','content_data','content_description',
              'date_created',('user', ('id','first_name','last_name','email','username',)))
    #exclude = ('id', re.compile(r'^private_'))
    model = Square
    def create(self, request, *args, **kwargs):
        '''
        api to create square.
        '''
#        if not request.user.is_authenticated():
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        squareForm =  CreateSquareForm(request.POST)
        if squareForm.is_valid():
            square = squareForm.save(commit=False)
            square.date_created = time.time()
            square.shared_count=0
            square.liked_count=0
            square.save()
            if square:
                successResponse['result'] = square
                return successResponse
            else:
                failureResponse['status'] = SYSTEM_ERROR
                failureResponse['error'] = "System Error."
                return 
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = squareForm.errors
            return failureResponse
        #return {"user":user}
        #return BaseHandler.create(self, request, *args, **kwargs)
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

class UserSelfFeedsHandler(BaseHandler):
    methods_allowed = ('GET',)
#    
    def read(self, request, user_id):
        squares = Square.objects.filter(user=user_id)
        if squares:
            successResponse['result']=squares
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
        if request.POST['square_id'].isdigit():
            squareObj = Square.objects.get(pk=request.POST['square_id'])
            userObj = User.objects.get(pk=1)
            userSquare = UserSquare(user=userObj, square =squareObj,date_shared=time.time()) 
            userSquare.save()
            squareObj.shared_count = squareObj.shared_count + 1
            squareObj.save()
            to_email = squareObj.user.email
            squareObj.id = None
            #saving copy of this square
            if request.POST['description']:
                squareObj.content_description = request.POST['description']
            squareObj.user = userObj
            squareObj.shared_count = 0
            squareObj.liked_count = 0
            squareObj.date_created = time.time()
            try:
                squareObj.full_clean()
                squareObj.save()
                # inform the owner 
                mailer = Emailer(subject=SUBJECT_SQUARE_ACTION_SHARED,body=BODY_SQUARE_ACTION_SHARED,from_email='coordinator@sqwag.com',to=to_email,date_created=time.time())
                mailentry(mailer)
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

class RelationshipHandler(BaseHandler):
    methods_allowed = ('GET','POST',)
    fields = ('id','date_subscribed','permission',('subscriber', ('id','first_name','last_name','email','username',)),
              ('producer', ('id','first_name','last_name','email','username',)))
    def create(self, request, *args, **kwargs):
        relationshipForm = CreateRelationshipForm(request.POST)
        if relationshipForm.is_valid():
            sub = relationshipForm.cleaned_data['subscriber']
            prod = relationshipForm.cleaned_data['producer']
            print sub.id
            print prod.id
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
    
    def read(self, request, user_id, *args, **kwargs):
        # only loged in user can get it's own feed
#        if not request.user.is_authenticated():
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        if user_id.isdigit():
            relationships = Relationship.objects.filter(subscriber=user_id)
            producers =  [relationship.producer for relationship in relationships]
            squares = Square.objects.filter(user__in=producers)
            if squares:
                successResponse['result'] = squares
                return successResponse
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "You need to subscribe to receive feeds"
                return failureResponse
        failureResponse['status'] = BAD_REQUEST
        failureResponse['error'] = "user_id is not an integer"
        return failureResponse
