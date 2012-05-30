'''
Created on 25-Apr-2012

@author: saini
'''
from django.core.exceptions import ValidationError
from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage
from sorl.thumbnail import *
from sqwag_api.models import *
import os
import tempfile
import time

def mailentry(mailer):
    mailer.is_sent=False
    mailer.status = "ignore"
    try:
        mailer.full_clean()
        mailer.save()
    except ValidationError, e :
        dummy = e.message() #TODO log error

def handle_uploaded_file(content_image,request):
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
    return 'assets/media/'+tempPath+'medium.jpg'
