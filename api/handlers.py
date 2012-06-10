from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, \
    ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from piston.handler import BaseHandler
from piston.utils import rc, throttle, validate
from sqwag_api.constants import *
from sqwag_api.forms import *
from sqwag_api.helper import *
from sqwag_api.models import *
import simplejson
import time

successResponse = {}
successResponse['status'] = SUCCESS_STATUS_CODE
successResponse['message'] = SUCCESS_MSG
failureResponse = {}

class SquareHandler(BaseHandler):
    allowed_methods = ('POST',)
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
        resultWrapper = crateSquare(request)
        return resultWrapper

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
                    wrapper = handle_uploaded_file(request.FILES['content_file'],request)
                    if wrapper['status']==SUCCESS_STATUS_CODE:
                        image_url = wrapper['result']
                    else:
                        return wrapper
                    square = form.save(commit=False)
                    square.content_type = "image"
                    square.content_data = image_url
                    resultWrapper = saveSquareBoilerPlate(request.user, square)
                    return resultWrapper
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
    allowed_methods = ('GET',)
    fields = ('id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',('user', ('id','first_name','last_name','email','username',)),(
              'user_account',('id','account_id','date_created','account_pic','account_handle','account')))
    #exclude = ('id', re.compile(r'^private_'))
    model = Square
    def read(self, request, page=1):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse 
        squares_all = Square.objects.filter(user=request.user).order_by('-date_created')
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

class ShareSquareHandler(BaseHandler):
    methods_allowed = ('POST',)
    successResponse = {}
    model = Square
    successResponse['status'] = SUCCESS_STATUS_CODE
    successResponse['message'] = SUCCESS_MSG
    failureResponse = {}
    def create(self,request, *args, **kwargs):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        if 'square_id' in request.POST:
            if request.POST['square_id'].isdigit():
                squareObj = Square.objects.get(pk=request.POST['square_id'])
                userObj = request.user
#                if(squareObj.user==userObj):
#                    failureResponse['status'] = DUPLICATE
#                    failureResponse['error'] = "you can not share your own square"
#                    return failureResponse
                userSquare = UserSquare(user=userObj, square =squareObj,date_shared=time.time()) 
                userSquare.save()
                squareObj.shared_count = squareObj.shared_count + 1
                squareObj.save()
                to_email = squareObj.user.email
                
                newSquare = Square(user=userObj,content_type=squareObj.content_type,content_src=squareObj.content_src,
                                   content_data=squareObj.content_data,date_created=time.time(),shared_count=0,
                                   liked_count=0)
                #saving copy of this square
                if 'description' in request.POST:
                    newSquare.content_description = request.POST['description']
                try:
                    #newSquare.full_clean(exclude='content_description')
                    newSquare.user_account = squareObj.user_account
                    newSquare.save()
                    # inform the owner 
                    mailer = Emailer(subject=SUBJECT_SQUARE_ACTION_SHARED,body=BODY_SQUARE_ACTION_SHARED,from_email='coordinator@sqwag.com',to=to_email,date_created=time.time())
                    mailentry(mailer)
                    userProfile = UserProfile.objects.get(user=newSquare.user)
                    userProfile.sqwag_count += 1
                    userProfile.save()
                    successResponse['result'] = newSquare
                    return successResponse
                except ValidationError, e :
                    squareObj.shared_count = squareObj.shared_count - 1
                    squareObj.save()
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = e.message
                    return failureResponse
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
                Relationship.objects.get(subscriber=sub, producer=prod)
                failureResponse['status'] = DUPLICATE
                failureResponse['error'] = "You are already following this user"
                return failureResponse
            except Relationship.DoesNotExist:
                # go ahead everything is fine
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

class GetFollowersHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_pic','account_handle','account_pic', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count')
    def read(self, request,id,page=1, *args, **kwargs):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        if id:
            try:
                user = User.objects.get(pk=id)
            except User.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = "user does not exist"#rc.FORBIDDEN
                return failureResponse
        else:
            user = request.user
        try:
            relationships =  Relationship.objects.filter(producer=user)
            if relationships.count() > 1:
                resultWrapper = relationshipPaginator(relationships, NUMBER_OF_SQUARES, page, user, 'subscriber')
                return resultWrapper
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "oops, no body is following you."
                return failureResponse
        except Relationship.DoesNotExist:
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "oops, no body is following you."
            return failureResponse

class GetProducersHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_pic','account_handle','account_pic', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count')
    def read(self, request,id,page=1, *args, **kwargs):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        if id:
            try:
                user = User.objects.get(pk=id)
            except User.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = "user does not exist"#rc.FORBIDDEN
                return failureResponse
        else:
            user = request.user
        try:
            relationships =  Relationship.objects.filter(subscriber=user)
            if relationships.count() > 1:
                resultWrapper = relationshipPaginator(relationships, NUMBER_OF_SQUARES, page, user, 'producer')
                return resultWrapper
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "oops, you are not following no body."
                return failureResponse
        except Relationship.DoesNotExist:
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "oops, you are not following no body"
            return failureResponse


class HomePageFeedHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',('user', ('id','first_name','last_name','email','username',)),(
              'user_account',('id','account_id','date_created','account_pic','account_handle','account')))
    #exclude = ('id', re.compile(r'^private_'))
    model = Square
    
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
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

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
                sq_obj.delete()  # TODO: SOFT DELETE REQUIRED. NOT HARD DELETE
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
    allowed_methods = ('GET',)
    fields = ('id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',('user', ('id','first_name','last_name','email','username',)),(
              'user_account',('id','account_id','date_created','account_pic','account_handle','account')))
    #exclude = ('id', re.compile(r'^private_'))
    model = Square
    def read(self, request, page=1, *args, **kwargs):
        # only authenticated user can get it's own feed
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        user = request.user
        relationships = Relationship.objects.filter(subscriber=user)
        producers =  [relationship.producer for relationship in relationships]
        squares_all = Square.objects.filter(user__in=producers).order_by('-liked_count','-shared_count','-date_created')
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

class TopPeopleHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_data','account_pic','account_handle','account_pic', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count')
    #exclude = ('id', re.compile(r'^private_'))
    def read(self, request, page=1, *args, **kwargs):
        # only authenticated user can get it's own feed
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        # get user profiles with most followers
        userProfiles = UserProfile.objects.all().order_by("-followed_by_count")
        #userProfiles = Square.objects.filter(user=request.user).order_by('-date_created')
        paginator = Paginator(userProfiles,NUMBER_OF_SQUARES)
        try:
            profiles = paginator.page(page)
            isNext = True
            if profiles.object_list:
                if int(page) >= paginator.num_pages:
                    isNext = False
                else:
                    isNext=True
                users = []
                for profile in profiles.object_list:
                    userObj = profile.user
                    useracc_obj = UserAccount.objects.filter(user=userObj)
                    userInfo = {}
                    userInfo['user'] = userObj
                    userInfo['user_profile'] = profile
                    userInfo['user_accounts']= useracc_obj
                    users.append(userInfo)
                successResponse['result'] = users
                successResponse['isNext'] = isNext
                successResponse['totalPages']= paginator.num_pages
                return successResponse
            else:
                failureResponse['status'] = NOT_FOUND
                failureResponse['error'] = "not much users on the platform. :("
                return failureResponse
        except PageNotAnInteger:
        # If page is not an integer, deliver failure response.
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "page should be an integer"
            return failureResponse
        except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
            failureResponse['status'] = NOT_FOUND
            failureResponse['error'] = "page is out of bounds"
        return failureResponse

class PublicSqwagsFeedsHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',('user', ('id','first_name','last_name','email','username',)),(
              'user_account',('id','account_id','date_created','account_pic','account_handle','account')))
    #exclude = ('id', re.compile(r'^private_'))
    model = Square
    
    def read(self, request, page=1, *args, **kwargs):
        squares_all = Square.objects.all().order_by('-date_created')
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

class UserInfo(BaseHandler):
    methods_allowed = ('GET')
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_pic','account_handle', 'sqwag_image_url',
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
        userInfo = getCompleteUserInfo(user_obj)
        return userInfo

class CommentsSquareHandler(BaseHandler):
    methods_allowed = ('GET','POST')
    fields = ('id','first_name','last_name','username','account','account_id','account_pic','sqwag_image_url',
             'content_src','content_type','content_data','content_description','date_created',
             'shared_count','liked_count','comment')
    def read(self,request,id):
#        if request.user.is_authenticated():
#                id = request.user.id
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        comments_info = []
        count = 0
        comments = SquareComments.objects.filter(square=id).order_by('date_created')
        for comment in comments:
            #user_comment = User.objects.get(comment.user)
            comment_array = {}
            comment_array['comment'] = comment
            comment_array['user'] = comment.user
            comments_info.append(comment_array)
            #comments_array['user'+str(count)] = comment.user
            count = count + 1            
        #user_account = UserAccount.objects.get(user=request.user)
        #square_user = User.objects.get(id=request.user.id)
        square = Square.objects.get(pk=id)
        #square_user_image = UserProfile.objects.get(user=square.user)
        square_user_info = {}
        square_user_info['user'] = square.user
        square_user_info['user_profile'] = UserProfile.objects.get(user=square.user)
        #user_comment = User.objects.get(comments.user)
        result = {}
        result['comments'] = comments_info
        result['square_account_info'] = square.user_account
        result['user_info'] = square_user_info
        result['square_info'] = square
        successResponse['result'] = result
        return successResponse
    
    def create(self,request, *args, **kwargs):
#        if not request.user.is_authenticated():
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"
#            return failureResponse
        if request.method == 'POST':
            commentForm =  CreateCommentsForm(request.POST)
            if commentForm.is_valid():
                comment = commentForm.save(commit=False)
                comment.date_created = time.time()
                comment.save()
                if comment:
                    successResponse['result'] = comment
                    return successResponse
            else:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['message'] = commentForm.errors
                return failureResponse                 
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['message'] = 'POST expected'
            return failureResponse
