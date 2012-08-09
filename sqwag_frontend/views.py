# Create your views here.
from django.shortcuts import render_to_response
from django.template.context import Context
from sqwag_api.helper import *

def index (request):
    if not request.user.is_authenticated():
        print "logged out"
        return render_to_response('index.html')
    print "logged in"
    complete_user = getCompleteUserInfo(request,request.user)
    c = Context(getUserContextObject(complete_user))
    return render_to_response('index.html',c)
