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
import array
import simplejson
import time

successResponse = {}
successResponse['status'] = SUCCESS_STATUS_CODE
successResponse['message'] = SUCCESS_MSG
failureResponse = {}

class SquareHandler(BaseHandler):
    allowed_methods = ('POST',)
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',)
    #exclude = ('id', re.compile(r'^private_'))
#    model = Square
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
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',)
#    model = Square
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
                    resultWrapper = saveSquareBoilerPlate(request, square)
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
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',)
    #exclude = ('id', re.compile(r'^private_'))
#    model = Square
    def read(self, request, page=1):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse 
        userSquares = UserSquare.objects.filter(user=request.user,is_deleted=False).order_by('-date_shared')
        squares_all = []
        visited = {}#this won't be required once resawaq for own sqwag is disabled
        for usrsquare in userSquares:
            # ignore this userSquare if this has already been entered into squares_all
            if not usrsquare.square.id in visited:
                square_obj = {}
                if not usrsquare.square.user_account:
                    account_type = 'NA'
                else:
                    account_type = usrsquare.square.user_account.id
                usrsquare.square.complete_user = getCompleteUserInfo(request,request.user,account_type)['result']
                square_obj['square'] = usrsquare.square
                usrsquare.complete_user = getCompleteUserInfo(request,request.user,account_type)['result']
                square_obj['userSquare'] = usrsquare
                squares_all.insert(0, square_obj)# optimize
                visited[usrsquare.square.id]=True
            else:
                # do nothing, ignore
                print 'ignore this square'
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

class ShareSquareHandler(BaseHandler):
    methods_allowed = ('POST',)
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',)
    successResponse = {}
#    model = Square
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
                is_owner = False
#                if(squareObj.user==userObj):
#                    failureResponse['status'] = DUPLICATE
#                    failureResponse['error'] = "you can not share your own square"
#                    return failureResponse
                userSquareObj = createUserSquare(request,userObj,squareObj,is_owner)
                if userSquareObj:
                    squareObj.shared_count = squareObj.shared_count + 1
                    squareObj.save()
                    squareResponse = {}
                    if not squareObj.user_account:
                        accountType = 'NA'
                    else:
                        accountType = squareObj.user_account.id
                    usrprofile = UserProfile.objects.get(user=request.user)
                    usrprofile.sqwag_count = usrprofile.sqwag_count + 1
                    usrprofile.save()
                    squareObj.complete_user = getCompleteUserInfo(request,squareObj.user,accountType)
                    squareResponse['square'] = squareObj
                    userSquareObj.complete_user = getCompleteUserInfo(request,request.user,'NA')
                    squareResponse['userSquare'] = userSquareObj
                    to_email = squareObj.user.email
                    # inform the owner 
                    mailer = Emailer(subject=SUBJECT_SQUARE_ACTION_SHARED,body=BODY_SQUARE_ACTION_SHARED,from_email='coordinator@sqwag.com',to=to_email,date_created=time.time())
                    mailentry(mailer)
                    successResponse['result'] = squareResponse 
                    #successResponse['result'] = newSquare
                    return successResponse
                else:
                    failureResponse['status'] = SYSTEM_ERROR
                    failureResponse['error'] = "some error occurred"
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
    fields = ('subscriber_complete_user','producer_complete_user','id','date_subscribed','permission',)
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
                relationship.producer_complete_user = getCompleteUserInfo(request,prod)
                relationship.subscriber_complete_user = getCompleteUserInfo(request,sub)
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
    def read(self,request,page=1,id=None, *args, **kwargs):
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
                resultWrapper = relationshipPaginator(request,relationships, NUMBER_OF_SQUARES, page, user, 'subscriber')
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
    def read(self, request,id=None,page=1, *args, **kwargs):
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
                resultWrapper = relationshipPaginator(request,relationships, NUMBER_OF_SQUARES, page, user, 'producer')
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
    fields = ('id','complete_user','date_shared','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created')
    #exclude = ('id', re.compile(r'^private_'))
#    model = Square
    
    def read(self, request, page=1, *args, **kwargs):
        # only authenticated user can get it's own feed
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        user = request.user
        relationships = Relationship.objects.filter(subscriber=user)
        producers =  [relationship.producer for relationship in relationships]
        userSquares = UserSquare.objects.filter(user__in=producers,is_deleted=False).order_by('date_shared')
        squares_all = []
        visited = {}
        for usrsquare in userSquares:
            # ignore this userSquare if this has already been entered into squares_all
            if not usrsquare.square.id in visited:
                square_obj = {}
                if not usrsquare.square.user_account:
                    accountType = 'NA'
                else:
                    accountType = usrsquare.square.user_account.id
                usrsquare.square.complete_user = getCompleteUserInfo(request,usrsquare.square.user,accountType)['result']
                square_obj['square'] = usrsquare.square
                usrsquare.complete_user = getCompleteUserInfo(request,usrsquare.user,'NA')['result']
                square_obj['userSquare'] = usrsquare
                squares_all.insert(0, square_obj)# optimize
                visited[usrsquare.square.id]=True
            else:
                # do nothing, ignore
                print 'ignore this square'
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper      

class DeleteSquareHandler(BaseHandler):
    methods_allowed = ('POST')
    
    def create(self, request, *args, **kwargs):
#        if not request.user.is_authenticated():
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        if "square_id" in request.POST:
            sq_id = request.POST['square_id']
            user_sq_obj = UserSquare.objects.get(pk=sq_id, user = '45')
            if user_sq_obj:
                if not user_sq_obj.is_owner:
                    userProfile = UserProfile.objects.get(user=user_sq_obj.user)
                    userProfile.sqwag_count = userProfile.sqwag_count - 1
                    userProfile.save()
                    user_sq_obj.is_deleted = True
                    user_sq_obj.save()  # TODO: SOFT DELETE REQUIRED. NOT HARD DELETE
                else:
                    squares_all = UserSquare.objects.filter(square=user_sq_obj.square)
                    square = Square.objects.get(pk=user_sq_obj.square.id)
                    square.is_deleted = True
                    square.save()
                    for sqrs in squares_all:
                        userProfile = UserProfile.objects.get(user=sqrs.user)
                        userProfile.sqwag_count = userProfile.sqwag_count - 1
                        userProfile.save()
                        sqrs.is_deleted = True
                        sqrs.save()
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
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count',
              'date_created')
#    exclude = ('username')
#    model = Square
    def read(self, request, page=1, *args, **kwargs):
        # only authenticated user can get it's own feed
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        topSquares = Square.objects.filter(is_deleted=False).order_by('-shared_count','-date_created')
        squares_all = []
        for topsqr in topSquares:
            square_obj = {}
            if not topsqr.user_account:
                accountType = 'NA'
            else:
                accountType = topsqr.user_account.id                
            usr = getCompleteUserInfo(request,topsqr.user,accountType)
            topsqr.complete_user = usr['result']
            square_obj['square'] = topsqr
            usrSqur = UserSquare.objects.get(square=topsqr,user=topsqr.user)
            usrSqur.complete_user = getCompleteUserInfo(request,topsqr.user,accountType)['result']
            square_obj['userSquare'] = usrSqur
            #square_obj['is_following'] = getRelationship(topsqr.user,request.user)             
            squares_all.append(square_obj)#optimize
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
                    userInfo = getCompleteUserInfo(request,userObj)
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
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',)
    #exclude = ('id', re.compile(r'^private_'))
#    model = Square
    
    def read(self, request, page=1, *args, **kwargs):
        topSquares = Square.objects.filter(is_deleted=False).order_by('-date_created')
        squares_all = []
        for topsqr in topSquares:
            square_obj = {}
            if not topsqr.user_account:
                accountType = 'NA'
            else:
                accountType = topsqr.user_account.id                
            usr = getCompleteUserInfo(request,topsqr.user,accountType)
            topsqr.complete_user = usr['result']
            square_obj['square'] = topsqr
            usrSqur = UserSquare.objects.get(square=topsqr,user=topsqr.user)
            usrSqur.complete_user = getCompleteUserInfo(request,topsqr.user,accountType)['result']
            square_obj['userSquare'] = usrSqur
            #square_obj['is_following'] = getRelationship(topsqr.user,request.user)             
            squares_all.append(square_obj)#optimize
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

class UserInfo(BaseHandler):
    methods_allowed = ('GET')
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_pic','account_handle', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count','display_name')
    
    def read(self,request,id=None,*args, **kwargs):
        if not id:
            if request.user.is_authenticated():
                id = request.user.id
            else:
                failureResponse['status'] = AUTHENTICATION_ERROR
                failureResponse['error'] = "Login Required"#rc.FORBIDDEN
                return failureResponse
        user_obj = User.objects.get(pk=id)
        userInfo = getCompleteUserInfo(request,user_obj)['result']
        return userInfo

class CommentsSquareHandler(BaseHandler):
    methods_allowed = ('GET','POST')
    fields = ('id','first_name','last_name','username','account','account_id','account_pic','sqwag_image_url',
             'content_src','content_type','content_data','content_description','date_created',
             'shared_count','liked_count','comment','displayname')
    def read(self,request,id,page=1):
#        if request.user.is_authenticated():
#                id = request.user.id
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        comments_info = []
        comments = SquareComments.objects.filter(square=id).order_by('date_created')
        if comments:    
            for comment in comments:
                comment_array = {}
                comment_array['comment'] = comment
                comment_array['user'] = getCompleteUserInfo(request,comment.user,'NA')['result']
                comments_info.append(comment_array)            
            resultWrapper = paginate(request, page, comments_info, NUMBER_OF_SQUARES)
            return resultWrapper
            return successResponse
        else:
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


class UserSquareHandler(BaseHandler):
    methods_allowed = ('GET')
    fields = ('complet_user','id','first_name','last_name','username','account','account_id','account_pic','sqwag_image_url',
             'content_src','content_type','content_data','content_description','date_created',
             'shared_count','liked_count','comment','displayname')
    
    def read(self,request,id):
#        if request.user.is_authenticated():
#                id = request.user.id
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        usrsquare = UserSquare.objects.get(pk=id,is_deleted=False)
        if usrsquare:
            result = {}
            square = usrsquare.square
            owner = usrsquare.square.user
            if not usrsquare.square.user_account.id:
                accountType = 'NA'
            else:
                accountType = usrsquare.square.user_account.id
            square.complete_user = getCompleteUserInfo(request,owner,accountType)['result']
            if  not usrsquare.is_owner:
                accountType = 'NA'
                usrsquare.complete_user = getCompleteUserInfo(request,usrsquare.user,accountType)['result']
                #square.sharing_user_content_description = usrsquare.content_description 
            else:
                usrsquare.complete_user = square.complete_user
            result['square'] = square
            result['userSquare'] = usrsquare    
            successResponse['result'] = result
            return successResponse
        
class restUserSquareHandler(BaseHandler):
    methods_allowed = ('GET')
    fields = ('complete_user','id','first_name','last_name','username','account','account_id','account_pic','sqwag_image_url',
             'content_src','content_type','content_data','content_description','date_created',
             'shared_count','liked_count','comment','displayname')
    def read(self,request,id):
#        if request.user.is_authenticated():
#                id = request.user.id
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        usrsquare = UserSquare.objects.get(pk=id)
        #print usrsquare.user
        usrsquares = UserSquare.objects.filter(square=usrsquare.square,is_deleted=False).order_by('-date_shared')
        result = {}
        squares_all = []
        for usrsqr in usrsquares:
            #print usrsqr.user
            if usrsqr.is_owner:
                print "ignore the owner"
            elif usrsqr == usrsquare:
                print "ignore the sharing user"
            else:
                usrsqr.complete_user = getCompleteUserInfo(request,usrsquare.user,'NA')['result']
                squares_all.append(usrsqr)
        successResponse['result'] = squares_all
        return successResponse
                
                
                
     
    
            
    
        
    