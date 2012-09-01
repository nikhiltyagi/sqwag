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
from sqwag_api.elasticsearch_api import *
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
                    resultWrapper = saveSquareBoilerPlate(request=request,user=request.user,square=square)
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
            failureResponse['error'] = 'POST expected'
            return failureResponse


class UserSelfFeedsHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created')
    def read(self, request, page=1):
        if not request.user.is_authenticated():
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse 
        userSquares = UserSquare.objects.filter(user=request.user,is_deleted=False,is_private=False).order_by('date_shared')
        #code for elastic search start
#        filter = {}
#        filter1 = CreateObject(type="term",typeindex="is_deleted",typevalue=False)
#        filter2 = CreateObject(type="term",typeindex="is_private",typevalue=False)
#        filter3 = CreateObject(type="term",typeindex="user_id",typevalue=request.user.id)
#        srt = CreateObject(type="date_shared",typeindex="order",typevalue="asc")
#        sort = [srt]
#        filter['and'] = [filter1,filter2,filter3]
#        result = GetDocument(url=ELASTIC_SEARCH_USERSQUARE_GET,filter=filter,sort=sort)
#        squares_all = []
#        for i in result:
#            sqr_obj = {}
#            query = CreateObject(type="term",typeindex="id",typevalue=i.square_id)
#            square = GetDocument(query,ELATIC_SEARCH_SQUARE_GET)
#            for x in square:
#                if not x.user_account_id:
#                    account_type = 'NA'
#                else:
#                    account_type = x.user_account_id
#            x.complete_user = getCompleteUserInfo(request,request.user,account_type)['result']
#            sqr_obj['square'] = x
#            i.complete_user = getCompleteUserInfo(request,request.user,account_type)['result']
#            sqr_obj['user_square'] = i
#            squares_all.insert(0,sqr_obj)
#        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
#        return resultWrapper
    #code for elastic search ends
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
                square_obj['user_square'] = usrsquare
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
                try:
                    usrSquare = UserSquare.objects.get(pk=request.POST['square_id'],is_deleted=False)
                except UserSquare.DoesNotExist:
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = 'square does not exist'
                    return failureResponse
                try:
                    squareObj = Square.objects.get(pk=usrSquare.square.id,is_deleted=False)
                except Square.DoesNotExist:
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = 'square to be reshared does not exist'
                userObj = request.user
                is_owner = False
                if(usrSquare.user==userObj):
                    failureResponse['status'] = DUPLICATE
                    failureResponse['error'] = "you can not share your own square"
                    return failureResponse
                userSquareObj = createUserSquare(request,userObj,squareObj,is_owner)
                notification = Notifications(user=usrSquare.user,sendingUser=request.user,userSquare=usrSquare)
                notification.notification_type = 'Reshare'
                notification.is_seen = False
                notification.date_created = time.time()
                notification.notification_message = ''
                notification.save()
                if userSquareObj:
                    squareObj.shared_count = squareObj.shared_count + 1
                    squareObj.save()
                    squareResponse = {}
                    if not squareObj.user_account:
                        accountId = 'NA'
                    else:
                        accountId = squareObj.user_account.id
                    try:
                        usrprofile = UserProfile.objects.get(user=request.user)
                    except UserProfile.DoesNotExist:
                        failureResponse['status'] = BAD_REQUEST
                        failureResponse['error'] = 'UserProfile does not exist'
                        return failureResponse
                    usrprofile.sqwag_count = usrprofile.sqwag_count + 1
                    usrprofile.save()
                    #code for elastic search start(tested and working fine)
                    #CreateDocument(Square.objects.get(pk=squareObj.id),squareObj.id,ELASTIC_SEARCH_SQUARE_POST)
                    #userdata = {}
                    #userdata['user_auth'] = User.objects.get(pk=request.user.id)
                    #userdata['user_profile'] = UserProfile.objects.get(user=request.user)  
                    #CreateDocument(userdata,request.user.id,ELASTIC_SEARCH_USER_POST)
                        #code for elastic search end
                    squareObj.complete_user = getCompleteUserInfo(request,squareObj.user,accountId)['result']
                    squareResponse['square'] = squareObj
                    userSquareObj.complete_user = getCompleteUserInfo(request,request.user,'NA')['result']
                    squareResponse['user_square'] = userSquareObj
                    to_email = usrSquare.user.email
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
                #code for elastic search starts(tested and working fine)
                #rel = Relationship.objects.get(subscriber=sub,producer=prod)
                #CreateDocument(rel,relationship.id,ELASTIC_SEARCH_RELATIONSHIP_POST)
                #code for elastic search ends
                #update producer's profile
                usr = relationship.producer
                userProfile = UserProfile.objects.get(user=usr)
                userProfile.followed_by_count += 1 
                userProfile.save()
                #code for elastic search starts(tested and working fine)
                #userdata = {}
                #userdata['user_auth'] = User.objects.get(pk=usr.id)
                #userdata['user_profile'] = UserProfile.objects.get(user=usr)
                #CreateDocument(userdata,usr.id,ELASTIC_SEARCH_USER_POST)
                #code for elastic search ends
                #update subscriber's profile
                usr = relationship.subscriber
                userProfile = UserProfile.objects.get(user=usr)
                userProfile.following_count += 1 
                userProfile.save()
                #code or elastic search starts(tested and working fine)
                #userdata = {}
                #userdata['user_auth'] = User.objects.get(pk=usr.id)
                #userdata['user_profile'] = UserProfile.objects.get(user=usr)
                #CreateDocument(userdata,usr.id,ELASTIC_SEARCH_USER_POST)
                #code for elastic search ends
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
               'sqwag_count','following_count','followed_by_count','displayname','fullname')
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
        #code for elastic start
#        query = CreateObject(type="term",typeindex="producer_id",typevalue=user.id)
#        not_res = CreateObject(type="term",typeindex="subscriber_id",typevalue=user.id)
#        filter = {"not" : not_res}
#        result = {"filtered" :{"query":query,"filter":filter}}
#        res = GetDocument(query=result,url=ELASTIC_SEARCH_RELATIONSHIP_GET)
#        if len(res) != 0:
#            rel_all = []
#            for i in res:
#                print i
#                rel_all.insert(0,i)
#            resultWrapper = relationshipPaginator(request,rel_all, NUMBER_OF_SQUARES, page, user, 'subscriber')
#            return resultWrapper
#        else:
#            failureResponse['status'] = NOT_FOUND
#            failureResponse['error'] = "oops, no body is following you."
#            return failureResponse
        #code for elastic search ends
        try:
            relationships =  Relationship.objects.filter(producer=user)            
            if relationships.count() > 1:
                resultWrapper = relationshipPaginator(request,relationships, NUMBER_OF_SQUARES, page, user, 'subscriber')
                print jsonpickle.encode(resultWrapper,unpicklable=True)
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
        #code for elastic search starts
#            query = CreateObject(type="term",typeindex="subscriber_id",typevalue=user.id)
#            not_res = CreateObject(type="term",typeindex="producer_id",typevalue=user.id)
#            filter = {"not" : not_res}
#            result = {"filtered" :{"query":query,"filter":filter}}
#            res = GetDocument(query=result,url=ELASTIC_SEARCH_RELATIONSHIP_GET)
#            if len(res) != 0:
#                rel_all = []
#                for i in res:
#                    print i
#                    rel_all.insert(0,i)
#                resultWrapper = relationshipPaginator(request,rel_all, NUMBER_OF_SQUARES, page, user, 'producer')
#                return resultWrapper
#            else:
#                failureResponse['status'] = NOT_FOUND
#                failureResponse['error'] = "oops, you are not following no body."
#                return failureResponse        
        #code for elastic search ends
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
        #code for elastic search start
#        query = CreateObject(type="term",typeindex="subscriber_id",typevalue=user.id)
#        result = GetDocument(query=query,url=ELASTIC_SEARCH_RELATIONSHIP_GET)
#        prducers = []
#        for i in result:
#            producer = i.producer_id
#            prducers.insert(0,producer)
#        print prducers
#        filter = {}
#        query = CreateObject(type="terms",typeindex="user_id",typevalue=prducers)
#        filter = CreateObject(type="term",typeindex="is_deleted",typevalue=False)
#        qry = {"filtered" :{"query":query,"filter":filter}}
#        result = GetDocument(query=qry,url=ELASTIC_SEARCH_USERSQUARE_GET)
#        sqrs_all = []
#        visited = {}
#        for i in result:
#            print i
#            if not i.square_id in visited:
#                square_obj = {}
#                query = CreateObject(type="term",typeindex="id",typevalue=i.square_id)
#                rslt = GetDocument(query=query,url=ELATIC_SEARCH_SQUARE_GET)
#                for l in rslt:
#                    if not l.user_account_id:
#                        accountId = 'NA'
#                    else:
#                        accountId = l.user_account_id
#                    sqr_obj = l
#                user = User.objects.get(pk=l.user_id)
#                l.complete_user = getCompleteUserInfo(request,user,accountId)['result']
#                user = User.objects.get(pk=i.user_id)
#                i.complete_user = getCompleteUserInfo(request,user,accountId)['result']
#                square_obj['square'] =  l
#                square_obj['user_square'] = i
#                visited[l.id]=True
#                sqrs_all.insert(0,square_obj)
#            else:
#                print "ignore this square"
#        resultWrapper = paginate(request, page, sqrs_all, NUMBER_OF_SQUARES)
#        return resultWrapper
        #code for elastic search end
        relationships = Relationship.objects.filter(subscriber=user)
        print relationships
        producers =  [relationship.producer for relationship in relationships]
        userSquares = UserSquare.objects.filter(user__in=producers,is_deleted=False).order_by('date_shared')
        print userSquares
        squares_all = []
        visited = {}
        for usrsquare in userSquares:
            # ignore this userSquare if this has already been entered into squares_all
            if not usrsquare.square.id in visited:
                square_obj = {}
                if not usrsquare.square.user_account:
                    accountId = 'NA'
                else:
                    accountId = usrsquare.square.user_account.id
                usrsquare.square.complete_user = getCompleteUserInfo(request,usrsquare.square.user,accountId)['result']
                square_obj['square'] = usrsquare.square
                usrsquare.complete_user = getCompleteUserInfo(request,usrsquare.user,'NA')['result']
                square_obj['user_square'] = usrsquare
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
            try:
                user_sq_obj = UserSquare.objects.get(pk=sq_id, user = request.user)
            except UserSquare.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = 'user square does not exist'
            if user_sq_obj:
                if not user_sq_obj.is_owner:
                    try:
                        userProfile = UserProfile.objects.get(user=user_sq_obj.user)
                    except UserProfile.DoesNotExist:
                        failureResponse['status'] = BAD_REQUEST
                        failureResponse['error'] = "user profile does not exists"
                        return failureResponse
                    userProfile.sqwag_count = userProfile.sqwag_count - 1
                    userProfile.save()
                    user_sq_obj.is_deleted = True
                    user_sq_obj.save()  # TODO: SOFT DELETE REQUIRED. NOT HARD DELETE
                else:
                    squares_all = UserSquare.objects.filter(square=user_sq_obj.square)
                    try:
                        square = Square.objects.get(pk=user_sq_obj.square.id,is_deleted=False)
                    except Square.DoesNotExist:
                        failureResponse['status'] = BAD_REQUEST
                        failureResponse['error'] = 'square does not exist'
                        return failureResponse
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
        #code for elastic start
#        query = CreateObject(type="term",typeindex="is_deleted",typevalue=False)
#        sort1 = CreateObject(type="shared_count",typeindex="order",typevalue="desc")
#        sort2 = CreateObject(type="date_created",typeindex="order",typevalue="desc")
#        sort = [sort1,sort2]
#        result = GetDocument(query=query,url=ELATIC_SEARCH_SQUARE_GET,sort=sort)
#        squares_all = []
#        for i in result:
#            print i
#            square_obj = {}
#            if not i.user_account_id:
#                accountId = "NA"
#            else:
#                accountId = i.user_account_id
#            i.complete_user = getCompleteUserInfo(request,User.objects.get(pk=i.id),accountId)['result']
#            filter1 = CreateObject(type="term",typeindex="square_id",typevalue=i.id)
#            filter2 = CreateObject(type="term",typeindex="user_id",typevalue=i.user_id)
#            filter = {}
#            filter['and'] = [filter1,filter2]
#            usersquare_result = GetDocument(url=ELASTIC_SEARCH_USERSQUARE_GET,filter=filter)
#            for j in usersquare_result:
#                j.complete_user = getCompleteUserInfo(request,User.objects.get(pk=i.id),accountId)['result']
#            square_obj['square'] = i
#            square_obj['user_square'] = j
#            squares_all.append(square_obj)
#        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
#        return resultWrapper
        #code for elastic search end
        topSquares = Square.objects.filter(is_deleted=False).order_by('-shared_count','-date_created')
        squares_all = []
        for topsqr in topSquares:
            square_obj = {}
            if not topsqr.user_account:
                accountId = 'NA'
            else:
                accountId = topsqr.user_account.id                
            usr = getCompleteUserInfo(request,topsqr.user,accountId)
            topsqr.complete_user = usr['result']
            square_obj['square'] = topsqr
            try:
                usrSqur = UserSquare.objects.get(square=topsqr,user=topsqr.user)
            except UserSquare.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = 'User square not found'
                return failureResponse
            usrSqur.complete_user = getCompleteUserInfo(request,topsqr.user,accountId)['result']
            square_obj['user_square'] = usrSqur
            #square_obj['is_following'] = getRelationship(topsqr.user,request.user)             
            squares_all.append(square_obj)#optimize
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        return resultWrapper

class TopPeopleHandler(BaseHandler):
    allowed_methods = ('GET',)
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_data','account_pic','account_handle','account_pic', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count','fullname','displayname')
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
        #code for elastic search start
#        sort = CreateObject(type="user_profile.followed_by_count",typeindex="order",typevalue="desc")
#        sort = [sort]
#        query = {"match_all" : {}}
#        result = GetDocument(query=query,url=ELASTIC_SEARCH_USER_GET,sort=sort)
#        userProfiles = []
#        for i in result:
#            print i
#            if not i['user_auth'].id == request.user.id:
#                userProfiles.append(i['user_profile'])
#            else:
#                print "ignore self"
        #code for elastic search end
        paginator = Paginator(userProfiles,8)
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
                    userInfo = getCompleteUserInfo(request,userObj)['result']
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
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count',
              'date_created',)
    #exclude = ('id', re.compile(r'^private_'))
#    model = Square
    
    def read(self, request, page=1, *args, **kwargs):
        #code for elastic search start
#        sort = CreateObject(type="date_created",typeindex="order",typevalue="desc")
#        sort = [sort]
#        query = {"match_all" : {}}
#        result = GetDocument(query=query,url=ELATIC_SEARCH_SQUARE_GET,sort=sort)
#        squaresAll = []
#        for res in result:
#            squareObj = {}
#            if not res.user_account_id:
#                accountId = 'NA'
#            else:
#                accountId = res.user_account_id
#            query = CreateObject(type="term",typeindex="user_auth.id",typevalue=res.user_id)
#            result = GetDocument(query=query,url=ELASTIC_SEARCH_USER_GET)
#            for i in result:
#                user = i['user_auth']
#            res.complete_user = getCompleteUserInfo(request,user,accountId)['result']
#            squareObj['square'] = res
#            filter1 = CreateObject(type="term",typeindex="square_id",typevalue=res.id)
#            filter2 = CreateObject(type="term",typeindex="user_id",typevalue=res.user_id)
#            filter3 = CreateObject(type="term",typeindex="is_private",typevalue=False)
#            filter = {}
#            filter['and'] = [filter1,filter2,filter3]
#            result = GetDocument(url=ELASTIC_SEARCH_USERSQUARE_GET,filter=filter)
#            for i in result:
#                usrSqur = i
#            usrSqur.complete_user = res.complete_user
#            squareObj['user_square'] = usrSqur
#            squaresAll.append(squareObj)
#        resultWrapper = paginate(request, page, squaresAll, 4)
#        return resultWrapper
        #code for elastic search end
        topSquares = Square.objects.filter(is_deleted=False).order_by('-date_created')
        squares_all = []
        for topsqr in topSquares:
            square_obj = {}
            if not topsqr.user_account:
                accountId = 'NA'
            else:
                accountId = topsqr.user_account.id
            usr = getCompleteUserInfo(request,topsqr.user,accountId)
            topsqr.complete_user = usr['result']
            square_obj['square'] = topsqr
            try:
                usrSqur = UserSquare.objects.get(square=topsqr,user=topsqr.user,is_private=False)
            except UserSquare.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = 'User square not found'
                return failureResponse
            usrSqur.complete_user = getCompleteUserInfo(request,topsqr.user,accountId)['result']
            square_obj['user_square'] = usrSqur
            #square_obj['is_following'] = getRelationship(topsqr.user,request.user)             
            squares_all.append(square_obj)#optimize
        resultWrapper = paginate(request, page, squares_all, 4)
        return resultWrapper

class UserInfo(BaseHandler):
    methods_allowed = ('GET')
    fields = ('id','first_name','last_name','email','username','account','account_id',
              'account_pic','account_handle', 'sqwag_image_url',
               'sqwag_count','following_count','followed_by_count','display_name','fullname')
    
    def read(self,request,id=None,*args, **kwargs):
        if not id:
            if request.user.is_authenticated():
                id = request.user.id
            else:
                failureResponse['status'] = AUTHENTICATION_ERROR
                failureResponse['error'] = "Login Required"#rc.FORBIDDEN
                return failureResponse
        try:
            user_obj = User.objects.get(pk=id)
        except User.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user does not exist'
        userInfo = getCompleteUserInfo(request,user_obj)
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
                failureResponse['error'] = commentForm.errors
                return failureResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'POST expected'
            return failureResponse


class UserSquareHandler(BaseHandler):
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
        #code for elastic start
#        filter1 = CreateObject(type="term",typeindex="id",typevalue=id)
#        filter2 = CreateObject(type="term",typeindex="is_deleted",typevalue=False)
#        filter = {}
#        filter['and'] = [filter1,filter2]
#        result = GetDocument(filter=filter,url=ELASTIC_SEARCH_USERSQUARE_GET)
#        if len(result) != 0:
#            for i in result:
#                userSquare = i
#                query = CreateObject(type="term",typeindex="user_auth.id",typevalue=i.user_id)
#                usr = GetDocument(query=query,url=ELASTIC_SEARCH_USER_GET)
#                for j in usr:
#                    user = j['user_auth']
#                
#                query = CreateObject(type="term",typeindex="id",typevalue=i.square_id)
#                sqr = GetDocument(query=query,url=ELATIC_SEARCH_SQUARE_GET)
#                for k in sqr:
#                    square = k
#                    query = CreateObject(type="term",typeindex="user_auth.id",typevalue=k.user_id)
#                    usr = GetDocument(query=query,url=ELASTIC_SEARCH_USER_GET)
#                    for j in usr:
#                        owner = j['user_auth']
#                    if k.user_account_id:
#                        accountId = j.user_account_id
#                    else:
#                        accountId = 'NA'
#                square.complete_user = getCompleteUserInfo(request,owner,accountId)['result']
#                if not userSquare.is_owner:
#                    accountId = 'NA'
#                    userSquare.complete_user = getCompleteUserInfo(request,user,accountId)['result']
#                else:
#                    userSquare.complete_user = square.complete_user
#            result = {}
#            result['square'] = square
#            result['user_square'] = userSquare    
#            successResponse['result'] = result
#            return successResponse 
#        else:
#            failureResponse['status'] = BAD_REQUEST
#            failureResponse['error'] = 'user square does not exist'
#            return failureResponse              
        #code for elastic search end
        try:
            usrsquare = UserSquare.objects.get(pk=id,is_deleted=False)
        except UserSquare.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user square does not exist'
            return failureResponse
        if usrsquare:
            result = {}
            square = usrsquare.square
            owner = usrsquare.square.user
            if not usrsquare.square.user_account:
                accountId = 'NA'
            else:
                accountId = usrsquare.square.user_account.id
            square.complete_user = getCompleteUserInfo(request,owner,accountId)['result']
            if  not usrsquare.is_owner:
                accountId = 'NA'
                usrsquare.complete_user = getCompleteUserInfo(request,usrsquare.user,accountId)['result']
                #square.sharing_user_content_description = usrsquare.content_description 
            else:
                usrsquare.complete_user = square.complete_user
            result['square'] = square
            result['user_square'] = usrsquare    
            successResponse['result'] = result
            return successResponse

class FeedbackHandler(BaseHandler):
    methods_allowed = ('GET','POST')
    fields = ('id', 'username','feedback','date_created')
    def create(self,request):
        if request.method =='POST':
            feedbackForm = FeedbackForm(request.POST)
            if feedbackForm.is_valid():
                feedback =  feedbackForm.cleaned_data['feedback']
                feedbackObj = Feedback(feedback=feedback, date_created = time.time())
                if not request.user.is_anonymous():
                    feedbackObj.user = request.user
                feedbackObj.save()
                successResponse['result']=feedbackObj
                return successResponse
            else:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = feedbackForm.errors
                return failureResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'Expecting a POST request'
            return failureResponse

class restUserSquareHandler(BaseHandler):
    methods_allowed = ('GET')
    fields = ('complete_user','id','first_name','last_name','username','account','account_id','account_pic','sqwag_image_url',
             'content_src','content_type','content_data','content_description','date_created',
             'shared_count','liked_count','comment','displayname')
    def read(self,request,id,page=1):
#        if request.user.is_authenticated():
#                id = request.user.id
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        #code for elastic search start
#        filter1 = CreateObject(type="term",typeindex="id",typevalue=id)
#        filter2 = CreateObject(type="term",typeindex="is_deleted",typevalue=False)
#        filter = {}
#        filter['and'] = [filter1,filter2]
#        result = GetDocument(filter=filter,url=ELASTIC_SEARCH_USERSQUARE_GET)
#        if len(result) != 0:
#            for i in result:
#                filter1 = CreateObject(type="term",typeindex="square_id",typevalue=i.square_id)
#                filter2 = CreateObject(type="term",typeindex="is_deleted",typevalue=False)
#                filter3 = CreateObject(type="term",typeindex="is_private",typevalue=False)
#                filter = {}
#                filter['and'] = [filter1,filter2,filter3]
#                sort = CreateObject(type="date_shared",typeindex="order",typevalue="desc")
#                sort = [sort]
#                query = {"match_all" : {}}
#                qry = {"filtered" :{"query":query,"filter":filter}}
#                userSquares = GetDocument(query=qry,url=ELASTIC_SEARCH_USERSQUARE_GET,sort=sort)
#                squares_all = []
#                for j in userSquares:
#                    userSquare = j
#                    if j.is_owner:
#                        print "ignore the owner"
#                    elif i==j:
#                        print "ignore the sharing user"
#                    else:
#                        query = CreateObject(type="term",typeindex="user_auth.id",typevalue=j.user_id)
#                        usr = GetDocument(query=query,url=ELASTIC_SEARCH_USER_GET)
#                        for k in usr:
#                            user = k['user_auth']
#                        userSquare.complete_user = getCompleteUserInfo(request,user,'NA')['result']
#                        squares_all.append(userSquare)
#            successResponse['result'] = squares_all
#            return successResponse
#        else:
#            failureResponse['status'] = BAD_REQUEST
#            failureResponse['error'] = 'user square does not exist'
#            return failureResponse        
        #code for elastic search end
        try:
            usrsquare = UserSquare.objects.get(pk=id)
        except UserSquare.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user square does not exist'
            return failureResponse
        #print usrsquare.user
        usrsquares = UserSquare.objects.filter(square=usrsquare.square,is_deleted=False,is_private=False).order_by('-date_shared')
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
        resultWrapper = paginate(request, page, squares_all, NUMBER_OF_SQUARES)
        successResponse['result'] = resultWrapper
        return successResponse
    
class unfollowHandler(BaseHandler):
    methods_allowed = ('GET')
    fields = fields = ('complete_user','id','first_name','last_name','username','account','account_id','account_pic','sqwag_image_url',
             'content_src','content_type','content_data','content_description','date_created',
             'shared_count','liked_count','comment','displayname')
    def read(self,request,id,*args,**kwargs):
        #        if request.user.is_authenticated():
        #                id = request.user.id
        #        else:
        #            failureResponse['status'] = AUTHENTICATION_ERROR
        #            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
        #            return failureResponse
        try:
            user = User.objects.get(pk=id)
        except User.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user to unfollow does not exist'
            return failureResponse
        try:
            RelationshipObj = Relationship.objects.get(subscriber=request.user,producer=user)
        except Relationship.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'you are not following this user'
            return failureResponse
        #code for elastic search starts(tested and working fine)
        #DeleteDocument(ELASTIC_SEARCH_RELATIONSHIP_POST,RelationshipObj.id)
        #code for elastic search ends
        RelationshipObj.delete()
        usrProfSubscriber = UserProfile.objects.get(user=request.user)
        usrProfSubscriber.following_count = usrProfSubscriber.following_count - 1
        usrProfSubscriber.save()
        #elastic search code starts(tested and working fine)
        #userdata = {}
        #userdata['user_auth'] = User.objects.get(pk=request.user.id)
        #userdata['user_profile'] = UserProfile.objects.get(user=request.user)
        #CreateDocument(userdata,request.user.id,ELASTIC_SEARCH_USER_POST)
        #elastic search code ends
        usrProfProducer = UserProfile.objects.get(user=user)
        usrProfProducer.followed_by_count = usrProfProducer.followed_by_count -1
        usrProfProducer.save()
        #elastic search code starts(tested and working fine)
        #userdata = {}
        #userdata['user_auth'] = User.objects.get(pk=user.id)
        #userdata['user_profile'] = UserProfile.objects.get(user=user)
        #CreateDocument(userdata,user.id,ELASTIC_SEARCH_USER_POST)
        #elastic search code ends
        successResponse['status'] = SUCCESS_STATUS_CODE
        successResponse['message'] = SUCCESS_MSG
        successResponse['result'] = 'successfully unfollowed the user'
        return successResponse

class notificationHandler(BaseHandler):
    methods_allowed = ('GET')
    fields = ('complete_user','sending_user','id','date_created','notification_type','notification_message')
    def read(self,request,page=1,*args,**kwargs):
        if request.user.is_authenticated():
            id = request.user.id
        else:
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        notifications = Notifications.objects.filter(user=request.user,is_seen=False)
        userNotifications = []
        for noti in notifications:
            noti.complete_user = getCompleteUserInfo(request,request.user,'NA')['result']
            noti.sending_user = getCompleteUserInfo(request,noti.sendingUser,'NA')['result']
            userNotifications.append(noti)
        resultWrapper = paginate(request, page, userNotifications, NUMBER_OF_SQUARES)
        if resultWrapper['status'] == SUCCESS_STATUS_CODE:
            seenNotifications = resultWrapper['result']
            for noti in seenNotifications:
                noti.is_seen = True
                noti.save()
        else:
            resultWrapper['status'] = SUCCESS_STATUS_CODE
            resultWrapper['message'] = 'No new notifications' #TODO : currently returning error message also need to remove this somehow
        return resultWrapper
    
class uploadCoverHandler(BaseHandler):
    methods_allowed = ('POST')
    fields = ('id','sqwag_image_url','sqwag_cover_image_url','personal_message','sqwag_count','following_count',
              'followed_by_count','displayname','username','first_name','last_name','email',)
    def create(self,request,*args,**kwargs):
        if request.user.is_authenticated():
            user=request.user
        else:
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        try:
            userProfile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user profile does not exist'
            return failureResponse
        if 'content_file' in request.FILES:
            wrapper = handle_uploaded_file(request.FILES['content_file'],request,'COVER')
            if wrapper['status']==SUCCESS_STATUS_CODE:
                userProfile.sqwag_cover_image_url = wrapper['result']
            else:
                return wrapper
            userProfile.save()
            #code or elastic search starts(tested and working fine)
            #userdata = {}
            #userdata['user_auth'] = User.objects.get(pk=user.id)
            #userdata['user_profile'] = UserProfile.objects.get(user=user)  
            #CreateDocument(userdata,user.id,ELASTIC_SEARCH_USER_POST)
            #code for elastic search ends
            successResponse['status'] = SUCCESS_STATUS_CODE
            successResponse['message'] = 'cover photo updated successfully'
            successResponse['result'] = userProfile
            return successResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "please select an image to upload"
            return failureResponse
        
class uploadProfilePictureHandler(BaseHandler):
    methods_allowed = ('POST')
    fields = ('id','sqwag_image_url','sqwag_cover_image_url','personal_message','sqwag_count','following_count',
              'followed_by_count','displayname',('user',('username','first_name','last_name','email',)))
    def create(self,request,*args,**kwargs):
        if request.user.is_authenticated():
            user=request.user
        else:
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        try:
            userProfile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user profile does not exist'
            return failureResponse
        if 'content_file' in request.FILES:
            wrapper = handle_uploaded_file(request.FILES['content_file'],request,'PROFILE')
            if wrapper['status']==SUCCESS_STATUS_CODE:
                userProfile.sqwag_image_url = wrapper['result']
            else:
                return wrapper
            userProfile.save()
            #code for elastic search starts(tested and working fine)
            #userdata = {}
            #userdata['user_auth'] = User.objects.get(pk=user.id)
            #userdata['user_profile'] = UserProfile.objects.get(user=user)  
            #CreateDocument(userdata,user.id,ELASTIC_SEARCH_USER_POST)
            #code for elastic search ends
            successResponse['status'] = SUCCESS_STATUS_CODE
            successResponse['message'] = 'profile pic updated successfully'
            successResponse['result'] = userProfile
            return successResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "please select an image to upload"
            return failureResponse
            
class uploadPersonalMessage(BaseHandler):
    methods_allowed = ('POST',)
    fields = ('id','sqwag_image_url','sqwag_cover_image_url','personal_message','sqwag_count','following_count',
              'followed_by_count','displayname',('user',('username','first_name','last_name','email',)))
    def create(self,request,*args,**kwargs):
        if request.user.is_authenticated():
            user=request.user
        else:
            failureResponse['status'] = AUTHENTICATION_ERROR
            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
            return failureResponse
        try:
            userProfile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = 'user profile does not exist'
            return failureResponse
        if 'message' in request.POST:
            userProfile.personal_message = request.POST['message']
            userProfile.save()
            #code for elastic search starts(tested and working fine)
            #userdata = {}
            #userdata['user_auth'] = User.objects.get(pk=user.id)
            #userdata['user_profile'] = UserProfile.objects.get(user=user)  
            #CreateDocument(userdata,user.id,ELASTIC_SEARCH_USER_POST)
            #code for elastic search ends
            successResponse['status'] = SUCCESS_STATUS_CODE
            successResponse['message'] = 'personal message updated successfully'
            successResponse['result'] = userProfile
            return successResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = "please set the message to be uploaded"
            return failureResponse

class sendSqwag(BaseHandler):
    methods_allowed = ('POST')
    def create(self,request,*args,**kwargs):
#        if request.user.is_authenticated():
#            user=request.user
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        user = User.objects.get(pk=49)
        form = SendSqwagForm(request.POST)
        if form.is_valid():
            usrSquareId = form.cleaned_data['userSquare']
            userName = form.cleaned_data['username']
            message = form.cleaned_data['message']
            try:
                usrSquare = UserSquare.objects.get(pk=usrSquareId)
            except UserSquare.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = 'user square to be sent does not exist'
                return failureResponse
            originalSquare = usrSquare.square
            try: 
                recievingUser = UserProfile.objects.get(username=userName)
            except User.DoesNotExist:
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = 'user to whom sqwag needs to be sent does not exist'
                return failureResponse
            try:
                UsrSqr = UserSquare.objects.get(user=recievingUser,square=originalSquare)
                failureResponse['status'] = BAD_REQUEST
                failureResponse['error'] = 'you can not send this sqwag to the user as he has already sqwagged/resqwagged it'
                return failureResponse
            except UserSquare.DoesNotExist:
                try:
                    privateusrsqr = UserSquare.objects.get(user=user,square=originalSquare,is_private=True)
                except UserSquare.DoesNotExist:
                    is_owner = False
                    is_private = True
                    privateusrsqr = createUserSquare(request,user,originalSquare,is_owner,is_private)
                    privateusrsqr.date_shared = time.time()
                    privateusrsqr.content_description = message
                    privateusrsqr.save()
                    #code for elastic search start
                    #CreateDocument(UserSquare.objects.get(pk=privateusrsqr.id),privateusrsqr.id,ELASTIC_SEARCH_USERSQUARE_POST)
                    #code for elastic search end
                noti = Notifications(user=recievingUser,userSquare=privateusrsqr,sendingUser=user,notification_type='square')
                noti.date_created = time.time()
                #noti.notification_message = message
                originalSquare.shared_count = originalSquare.shared_count + 1
                originalSquare.save()
                #code for elastic search start
                #CreateDocument(Square.objects.get(pk=originalSquare.id),originalSquare.id,ELASTIC_SEARCH_SQUARE_POST)
                #code for elastic search end
                noti.save()
                privateSquare = PrivateSquare(user=recievingUser,userSquare=privateusrsqr)
                privateSquare.save()
                successResponse['status'] = SUCCESS_STATUS_CODE
                successResponse['message'] = 'square successfully sent'
                return successResponse
        else:
            failureResponse['status'] = BAD_REQUEST
            failureResponse['error'] = form.errors
            return failureResponse
        
class recieveSqwag(BaseHandler):
    methods_allowed = ('POST')
    fields = ('complete_user','id','content_src','content_type','content_data','content_description','shared_count','liked_count',
              'date_created',)
    def create(self,request,*args,**kwargs):
#        if request.user.is_authenticated():
#            user=request.user
#        else:
#            failureResponse['status'] = AUTHENTICATION_ERROR
#            failureResponse['error'] = "Login Required"#rc.FORBIDDEN
#            return failureResponse
        if 'square_id' in request.POST:
            if request.POST['square_id'].isdigit():
                try:
                    usrSquare = UserSquare.objects.get(pk=request.POST['square_id'],is_deleted=False,is_private=True)
                except UserSquare.DoesNotExist:
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = 'square does not exist'
                    return failureResponse
                try:
                    squareObj = Square.objects.get(pk=usrSquare.square.id,is_deleted=False)
                except Square.DoesNotExist:
                    failureResponse['status'] = BAD_REQUEST
                    failureResponse['error'] = 'square to be reshared does not exist'
                userObj = request.user
                is_owner = False
                if(squareObj.user==userObj):
                    failureResponse['status'] = DUPLICATE
                    failureResponse['error'] = "you can not share your own square"
                    return failureResponse
                userSquareObj = createUserSquare(request,userObj,squareObj,is_owner)
                if userSquareObj:
                    squareObj.shared_count = squareObj.shared_count + 1
                    squareObj.save()
                    #code for elastic search start
                    #CreateDocument(Square.objects.get(pk=squareObj.id),squareObj.id,ELASTIC_SEARCH_SQUARE_POST)
                    #code for elastic search end
                    squareResponse = {}
                    if not squareObj.user_account:
                        accountId = 'NA'
                    else:
                        accountId = squareObj.user_account.id
                    try:
                        usrprofile = UserProfile.objects.get(user=request.user)
                    except UserProfile.DoesNotExist:
                        failureResponse['status'] = BAD_REQUEST
                        failureResponse['error'] = 'UserProfile does not exist'
                        return failureResponse
                    usrprofile.sqwag_count = usrprofile.sqwag_count + 1
                    usrprofile.save()
                    #code for elastic search start
#                    userdata = {}
#                    userdata['user_auth'] = User.objects.get(pk=request.user.id)
#                    userdata['user_profile'] = UserProfile.objects.get(user=request.user)  
                    #CreateDocument(userdata,request.user.id,ELASTIC_SEARCH_USER_POST)
                    #code for elastic search end    
                    squareObj.complete_user = getCompleteUserInfo(request,squareObj.user,accountId)
                    squareResponse['square'] = squareObj
                    userSquareObj.complete_user = getCompleteUserInfo(request,request.user,'NA')
                    squareResponse['user_square'] = userSquareObj    
                    to_email = usrSquare.user.email
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
        
    
    