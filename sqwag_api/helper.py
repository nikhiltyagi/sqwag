'''
Created on 25-Apr-2012

@author: saini
'''
from django.core.exceptions import ValidationError
from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from sorl.thumbnail import *
from sqwag_api.constants import *
from sqwag_api.forms import *
from sqwag_api.models import *
import os
import tempfile
import time
from twisted.python.reflect import ObjectNotFound

def mailentry(mailer):
    mailer.is_sent=False
    mailer.status = "ignore"
    try:
        mailer.full_clean()
        mailer.save()
    except ValidationError, e :
        dummy = e.message() #TODO log error

def handle_uploaded_file(content_image,request):
    resultWrapper = {}
    try:
        time_created = time.time()
        tempPath = 'user_image/'+ str(request.user.id)+'/'+str(time_created)+'/'
        print tempPath
        path = default_storage.save(tempPath+'original.jpg', ContentFile(content_image.read()))
        tmp_file = os.path.join(settings.MEDIA_ROOT, path)
        image = open(tmp_file)
        small_image = get_thumbnail(image, '100x100', crop='center', quality=99)
        default_storage.save(tempPath+'small.jpg', ContentFile(small_image.read()))
        medium_image = get_thumbnail(image, '220x220', crop='center', quality=99)
        default_storage.save(tempPath+'medium.jpg', ContentFile(medium_image.read()))
        large_image = get_thumbnail(image, '500x500', crop='center', quality=99)
        default_storage.save(tempPath+'large.jpg', ContentFile(large_image.read()))
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
        resultWrapper = saveSquareBoilerPlate(request.user, square)
    else:
        resultWrapper['status'] = BAD_REQUEST
        resultWrapper['error'] = squareForm.errors
        return resultWrapper

def saveSquareBoilerPlate(user, square):
    resultWrapper = {}
    square.date_created = time.time()
    square.shared_count=0
    square.liked_count=0
    square.user = user
    if square.content_src == 'twitter.com':
        try:
            userAccount = UserAccount.objects.get(user=user,account='twitter.com')
            square.user_account = userAccount
        except UserAccount.DoesNotExist:
            print "user account twitter does not exist"
    elif square.content_src == 'instagram.com':
        try:
            userAccount = UserAccount.objects.get(user=user,account='instagram.com')
            square.user_account = userAccount
        except UserAccount.DoesNotExist:
            print "user account instagram does not exist"
    square.save()
    try:
        userProfile = UserProfile.objects.get(user=square.user)
        userProfile.sqwag_count += 1
        userProfile.save()
    except UserProfile.DoesNotExist:
        resultWrapper['status'] = SYSTEM_ERROR
        resultWrapper['error'] = "user profile does not exist. user is: " + user.first_name
        return resultWrapper
    if square:
        resultWrapper['status']= SUCCESS_STATUS_CODE
        resultWrapper['result'] = square
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

def getCompleteUserInfo(user):
    resultWrapper = {}
    userInfo = {}
    if user:
        try:
            useracc_obj = UserAccount.objects.filter(user=user)
            userProfile = UserProfile.objects.get(user=user)
            userInfo['user'] = user
            userInfo['user_profile'] = userProfile
            userInfo['user_accounts']= useracc_obj
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

def relationshipPaginator(relationships,itemsPerPage,page,user,userType):
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
                    userInfo = getCompleteUserInfo(userObj)
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
