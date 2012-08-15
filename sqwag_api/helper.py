'''
Created on 25-Apr-2012

@author: saini
'''
from StringIO import StringIO
from django.core.exceptions import ValidationError
from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from sorl.thumbnail import *
from sqwag_api.InstaService import *
from sqwag_api.constants import *
from sqwag_api.elsaticsearch import *
from sqwag_api.forms import *
from sqwag_api.models import *
from twisted.python.reflect import ObjectNotFound
import Image
import cStringIO
import os
import tempfile
import time
from twisted.python.reflect import ObjectNotFound
from sqwag_api.elsaticsearch import *
from sqwag_api.elasticsearch_api import *
import urllib


def mailentry(mailer):
    mailer.is_sent=False
    mailer.status = "ignore"
    try:
        mailer.full_clean()
        mailer.save()
    except ValidationError, e :
        dummy = e.message() #TODO log error

def handle_uploaded_file(content_image,request=None,imageType=None,user=None):
    resultWrapper = {}
    try:
        time_created = time.time()
        if user is not None:
            user_id = user.id
        else:
            user_id = request.user.id
        tempPath = 'user_image/'+ str(user_id)+'/'+str(time_created)+'/'
        print tempPath
        f = content_image.read()
        path = default_storage.save(tempPath+'original.jpg', ContentFile(f))
        tmp_file = os.path.join(settings.MEDIA_ROOT, path)
        image = open(tmp_file)
        small_image = get_thumbnail(image, '52x52', crop='center', quality=99)
        default_storage.save(tempPath+'small.jpg', ContentFile(small_image.read()))
        medium_image = get_thumbnail(image, '240x240', crop='center', quality=99)
        default_storage.save(tempPath+'medium.jpg', ContentFile(medium_image.read()))
        large_image = get_thumbnail(image, '500x500', crop='center', quality=99)
        default_storage.save(tempPath+'large.jpg', ContentFile(large_image.read()))
        if imageType == 'COVER':
            cover_image = get_thumbnail(image, '220x440', crop='center', quality=99)
            default_storage.save(tempPath+'cover.jpg', ContentFile(cover_image.read()))
            resultWrapper['status']=SUCCESS_STATUS_CODE
            resultWrapper['result']= 'assets/media/'+tempPath+'cover.jpg'
            return resultWrapper
        elif imageType == 'PROFILE':
            resultWrapper['status']=SUCCESS_STATUS_CODE
            resultWrapper['result']= 'assets/media/'+tempPath+'small.jpg'
            return resultWrapper
        else:
            resultWrapper['status']=SUCCESS_STATUS_CODE
            resultWrapper['result']= 'assets/media/'+tempPath+'medium.jpg'
            return resultWrapper
    except IOError, e:
        resultWrapper['status']='file error'
        resultWrapper['error']= e.message
        return resultWrapper

def crateSquare(request):
    resultWrapper = {}
    squareForm =  CreateSquareForm(request.POST)
    if squareForm.is_valid():
        square = squareForm.save(commit=False)
        resultWrapper = saveSquareBoilerPlate(request=request,user=request.user, square=square)
        return resultWrapper
    else:
        resultWrapper['status'] = BAD_REQUEST
        resultWrapper['error'] = squareForm.errors
        return resultWrapper

def saveSquareBoilerPlate(request=None,user=None, square=None, date_created=None):
    resultWrapper = {}
    if date_created:
        square.date_created = date_created
    else:
        square.date_created = time.time()
    #user =request.user
    square.shared_count=0
    square.user = user
    if square.content_src == 'twitter.com':
        try:
            userAccount = UserAccount.objects.get(user=user,account=ACCOUNT_TWITTER,is_active=True)
            square.user_account = userAccount
        except UserAccount.DoesNotExist:
            print "user account twitter does not exist"
    elif square.content_src == 'instagram.com':
        try:
            userAccount = UserAccount.objects.get(user=user,account=ACCOUNT_INSTAGRAM,is_active=True)
            square.user_account = userAccount
        except UserAccount.DoesNotExist:
            print "user account instagram does not exist"
    square.save()
    #code for elastic search start
    #CreateDocument(Square.objects.get(pk=square.id),square.id,ELASTIC_SEARCH_SQUARE_POST)
    #code for elastic search ends
    is_owner = True
    squareResponse = {}
    userSquare = createUserSquare(None,user,square,is_owner)
    try:
        userProfile = UserProfile.objects.get(user=square.user)
        userProfile.sqwag_count += 1
        userProfile.save()
    except UserProfile.DoesNotExist:
        resultWrapper['status'] = SYSTEM_ERROR
        resultWrapper['error'] = "user profile does not exist. user is: " + user.first_name
        return resultWrapper
    if square:
        if not square.user_account:
            accountType = 'NA'
        else:
            accountType = square.user_account.id
        square.complete_user =  getCompleteUserInfo(request,user,accountType)['result']
        userSquare.complete_user = square.complete_user
        squareResponse['square'] = square
        squareResponse['user_square'] = userSquare
        resultWrapper['status']= SUCCESS_STATUS_CODE
        resultWrapper['result'] = squareResponse
        return resultWrapper
    else:
        resultWrapper['status'] = SYSTEM_ERROR
        resultWrapper['error'] = "System Error."
        return resultWrapper

def paginate(request, page, inputList, itemsPerPage):
    resultWrapper = {}
    paginator = Paginator(inputList,itemsPerPage)
    try:
        objects = paginator.page(page)
        isNext = True
        if objects.object_list:
            if int(page) >= paginator.num_pages:
                isNext = False
            else:
                isNext=True
            resultWrapper['status'] = SUCCESS_STATUS_CODE
            resultWrapper['result'] = objects.object_list
            resultWrapper['isNext'] = isNext
            resultWrapper['totalPages']= paginator.num_pages
            return resultWrapper
        else:
            resultWrapper['status'] = NOT_FOUND
            resultWrapper['error'] = "No sqwags by you :(. Start sqwagging, it's really easy :)"
        return resultWrapper
    except PageNotAnInteger:
    # If page is not an integer, deliver failure response.
        resultWrapper['status'] = BAD_REQUEST
        resultWrapper['error'] = "page should be an integer"
        return resultWrapper
    except EmptyPage:
    # If page is out of range (e.g. 9999), deliver last page of results.
        resultWrapper['status'] = NOT_FOUND
        resultWrapper['error'] = "page is out of bounds"
    return resultWrapper

def getCompleteUserInfo(request=None,user=None,accountType=None):
    resultWrapper = {}
    userInfo = {}
    if user:
    #code for elastic search start
#        query = CreateObject(type="term",typeindex="user_auth.id",typevalue=user.id)
#        result = GetDocument(query=query,url=ELASTIC_SEARCH_USER_GET)
#        for i in result:
#            print i
#            userInfo['user'] = GetUser(i['user_auth'])
#            userInfo['user_profile'] = GetUserProfile(i['user_profile'])
#        filter = {}  
#        if not accountType:
#            useracc_obj = []
#            fields = ["account","account_pic","account_handle","py/object","id","account_id","account_data"]
#            filter1 = CreateObject(type="term",typeindex="user_id",typevalue=user.id)
#            filter2 = CreateObject(type="term",typeindex="is_active",typevalue=True)
#            filter['and'] = [filter1,filter2]
#            result = GetDocument(filter=filter,url=ELASTIC_SEARCH_USERACCOUNT_GET,fields=fields)
#            jsoncontent = jsonpickle.decode(result)
#            for i in jsoncontent['hits']['hits']:
#                print i['fields']
#                useracc_obj.insert(0,i['fields'])
#        elif accountType=='NA':
#            useracc_obj = {}
#        else:
#            useracc_obj = []
#            fields = ["account","account_pic","account_handle","py/object"]
#            filter1 = CreateObject(type="term",typeindex="user_id",typevalue=user.id)
#            filter2 = CreateObject(type="term",typeindex="is_active",typevalue=True)
#            filter3 = CreateObject(type="term",typeindex="account",typevalue=accountType)
#            filter['and'] = [filter1,filter2,filter3]
#            result = GetDocument(filter=filter,url=ELASTIC_SEARCH_USERACCOUNT_GET,fields=fields)
#            jsoncontent = jsonpickle.decode(result)
#            for i in jsoncontent['hits']['hits']:
#                print i['fields']
#                useracc_obj.insert(0,i['fields'])            
#        userInfo['user_accounts']= useracc_obj
#        if request is not None and not request.user.is_anonymous():
#            userInfo['is_following'] = False
#            filter1 = CreateObject(type="term",typeindex="subscriber_id",typevalue=request.user.id)
#            filter2 = CreateObject(type="term",typeindex="producer_id",typevalue=user.id)
#            filter['and'] = [filter1,filter2]
#            result = GetDocument(filter=filter,url=ELASTIC_SEARCH_RELATIONSHIP_GET)
#            #jsoncontent = jsonpickle.decode(result)
#            for i in result:
#                userInfo['is_following'] = True
#        resultWrapper['status']=SUCCESS_STATUS_CODE
#        resultWrapper['result']=userInfo
#        return resultWrapper                          
    #code for elastic search end
        try:
            userProfile = UserProfile.objects.values("following_count","followed_by_count","displayname","sqwag_count",
                                                     "sqwag_image_url","sqwag_cover_image_url","username","fullname","personal_message").get(user=user)
            userInfo['user'] = User.objects.values("username","first_name","last_name","email","id").get(pk=user.id)#TODO : change this.this is bad
            userInfo['user_profile'] = userProfile
            if not accountType:
                useracc_obj = UserAccount.objects.values("account","account_pic","account_handle").filter(user=user,is_active=True)
            elif accountType=='NA':
                useracc_obj = {}
            else:    
                useracc_obj = UserAccount.objects.values("account","account_pic","account_handle").get(user=user,account=accountType,is_active=True)
            userInfo['user_accounts']= useracc_obj
            if request is not None and not request.user.is_anonymous():
                try:
                    Relationship.objects.get(subscriber=request.user,producer=user)
                    userInfo['is_following'] = True
                except Relationship.DoesNotExist:
                    userInfo['is_following'] = False
            resultWrapper['status']=SUCCESS_STATUS_CODE
            resultWrapper['result']=userInfo
            return resultWrapper
        except UserProfile.DoesNotExist:
            resultWrapper['status']=SYSTEM_ERROR
            resultWrapper['error']= 'user profile does not exist'
            return resultWrapper
    else:
        resultWrapper['status']=BAD_REQUEST
        resultWrapper['error']='user object is null'
        return resultWrapper;

def relationshipPaginator(request,relationships,itemsPerPage,page,user,userType):
    resultWrapper = {}
    paginator = Paginator(relationships,itemsPerPage)
    try:
        relatives = paginator.page(page)
        isNext = True
        if relatives.object_list:
            if int(page) >= paginator.num_pages:
                isNext = False
            else:
                isNext=True
            users = []
            for relative in relatives.object_list:
                if userType=='producer':
                    userObj = relative.producer
                else:
                    userObj = relative.subscriber
                if userObj==user:
                    print "ignore self" # log it
                else:
                    userInfo = getCompleteUserInfo(request,userObj)
                    if userInfo['status'] == SUCCESS_STATUS_CODE:
                        users.append(userInfo['result'])
                        resultWrapper['status'] = SUCCESS_STATUS_CODE
                        resultWrapper['result'] = users
                        resultWrapper['isNext'] = isNext
                        resultWrapper['totalPages']= paginator.num_pages
                    else:
                        print userInfo['error'] # log it
            return resultWrapper
        else:
            resultWrapper['status'] = NOT_FOUND
            resultWrapper['error'] = "oops, you are not following no body."
            return resultWrapper
    except PageNotAnInteger:
    # If page is not an integer, deliver failure response.
        resultWrapper['status'] = BAD_REQUEST
        resultWrapper['error'] = "page should be an integer"
        return resultWrapper
    except EmptyPage:
    # If page is out of range (e.g. 9999), deliver last page of results.
        resultWrapper['status'] = NOT_FOUND
        resultWrapper['error'] = "page is out of bounds"
        return resultWrapper

def createUserSquare(request,user,square,is_owner,is_private=False):
    userSquare = UserSquare(user=user,square=square)
    userSquare.date_shared = time.time()
    userSquare.is_deleted = False
    if is_owner:
        userSquare.content_description = square.content_description
    else:
        if 'content_desc' in request.POST:
            form = ContentDescriptionForm(request.POST)
            if form.is_valid():
                userSquare.content_description = request.POST['content_desc']
        else:
            userSquare.content_description = ""        
    userSquare.is_owner = is_owner
    if is_private:
        userSquare.is_private = True
    userSquare.save()
    #code for elasti search starts
    #CreateDocument(UserSquare.objects.get(pk=userSquare.id),userSquare.id,ELASTIC_SEARCH_USERSQUARE_POST)
    #code for elastic search ends
    return userSquare

def getRelationship(producer,subscriber):
    user = Relationship.objects.get(producer=producer,subscriber=subscriber)
    if user:
        is_following = True
    else:
        is_following = False
    return is_following

def getActiveUserAccount(user, account):
    try:
        user = User.objects.get(pk=user)
        return UserAccount.objects.get(user=user, account=account,is_active=True)
    except:
        return UserAccount.objects.get(user=user, account=account,is_active=True)

        
def syncInstaFeed(insta_user_id=None ):
    #access_token ='52192801.6e7b6c7.d45ef561f92b414f8e0c9630220b3c09'
    print("inside syncINstaFeed")
    if insta_user_id is not None:
        print("getting userAccount")
        userAccount = UserAccount.objects.get(account_id=insta_user_id,
                                                            account=ACCOUNT_INSTAGRAM, is_active=True)
        print("userAccount obtained")
        if userAccount.last_object_id:
            min_id = userAccount.last_object_id
            print "last min_id was: "+ str(min_id)
        else:
            min_id=1
        print("min id is "+str(min_id))
        print("calling insta api for recent user feed")
        content = getUserRecentFeed(min_id=min_id,
                                    access_token=userAccount.access_token,
                                    user_id=insta_user_id);
        #content is an Object
        objects =  content['data']
        for object in reversed(objects):
            createInstaSquare(object=object, insta_user_id=object['user']['id'])
        #store the first object's id as the last_object_id in userAccount table
        userAccount.last_object_id = objects[0]['id']
        userAccount.save()
        print "new min_id is: "+ str(object['id'])
    else:
        print ("user is none, syncInstaFeed not possible")
    return content

def createInstaSquare(object=None, insta_user_id=None):
    if object is not None and insta_user_id is not None:
        img_url=object['images']['standard_resolution']['url']
        print img_url
        img = urllib.urlopen(img_url)
        try:
            userAccount = UserAccount.objects.get(account_id=insta_user_id, account=ACCOUNT_INSTAGRAM, is_active=True)
            wrapper = handle_uploaded_file(img,user=userAccount.user)
            if wrapper['status']==SUCCESS_STATUS_CODE:
                image_url = wrapper['result']
            #check if square exists for this feed
            try:
                sqwagUser = userAccount.user
                Square.objects.get(user=sqwagUser, content_id=object['id'])
                print ("ignore this object, it is already in database")
            except Square.DoesNotExist:
                # now create a square of this object by this sqwag user
                square = Square(user=sqwagUser, content_type='insta_image', content_src='instagram.com', 
                                content_id=object['id'],content_data=image_url,
                                 date_created=object['created_time'],shared_count=0)
                square.user_account = userAccount
                
                if object['caption'] is not None:
                    square.content_description=object['caption']['text']
                try:
                    square.full_clean(exclude='content_description')
                    square.save()
                    saveSquareBoilerPlate(user=square.user, square=square, date_created=square.date_created)
                except ValidationError:
                    print  "error in saving square"# TODO: log this
        except UserAccount.DoesNotExist:
            print "user account does not exist"
    else:
        print "invalid arguments"
        return None
    
def CreateUserAccount(user=None,account=None,account_id=None,access_token=None,account_data=None
                      ,account_pic= None,account_handle=None,is_active=True,last_object_id=0):
    userAccount = UserAccount(user=user,account=account,account_id=account_id,access_token=access_token,
                              date_created=time.time(),account_data=account_data,account_pic=account_pic,
                              account_handle=account_handle,is_active=is_active,last_object_id=0)
    return userAccount

def GetUser(user=None):
    userdata = {}
    userdata['username'] = user.username
    userdata['first_name'] = user.first_name
    userdata['last_name'] = user.last_name
    userdata['email'] = user.email
    userdata['id'] = user.id
    return userdata

def GetUserProfile(userProf=None):
    userdata = {}
    userdata['username'] = userProf.username
    userdata['displayname'] = userProf.displayname
    userdata['fullname'] = userProf.fullname
    userdata['following_count'] = userProf.following_count
    userdata['sqwag_count'] = userProf.sqwag_count
    userdata['personal_message'] = userProf.personal_message
    userdata['followed_by_count'] = userProf.followed_by_count
    userdata['sqwag_image_url'] = userProf.sqwag_image_url
    userdata['sqwag_cover_image_url'] = userProf.sqwag_cover_image_url
    return userdata
