from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from piston.handler import BaseHandler
from piston.utils import rc, throttle, validate
from sqwag_api.constants import *
from sqwag_api.forms import CreateSquareForm
from sqwag_api.models import Square
import simplejson
import time

successResponse = {}
successResponse['status'] = SUCCESS_STATUS_CODE
successResponse['message'] = SUCCESS_MSG
failureResponse = {}
class SquareHandler(BaseHandler):
    allowed_methods = ('GET', 'PUT', 'DELETE','POST')
    fields = ('id','content_src','content_type','content_data', 'testme',
              'date_created',('user', ('id','first_name','last_name','email','username',)))
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
    
#    def testme(self, square):
#        return square
#    def read(self, request, id):
#        square = Square.objects.get(id)
#        return square
#
#    @throttle(5, 10*60) # allow 5 times in 10 minutes
#    def update(self, request, id):
#        square = Square.objects.get(id)
#        square.data = request.PUT.get('data')
#        square.save()
#        return square
#
#    def delete(self, request, id):
#        square = Square.objects.get(id)
#        if not request.user == square.author:
#            return rc.FORBIDDEN # returns HTTP 401
#        square.delete()
#        return rc.DELETED # returns HTTP 204
    
#
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
#        return { 'user': user, 'data_length': len(data) }