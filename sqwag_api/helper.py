'''
Created on 25-Apr-2012

@author: saini
'''
from django.core.exceptions import ValidationError
from sqwag_api.models import *
def mailentry(mailer):
    mailer.is_sent=False
    mailer.status = "ignore"
    try:
        mailer.full_clean()
        mailer.save()
    except ValidationError, e :
        dummy = e.message() #TODO log error