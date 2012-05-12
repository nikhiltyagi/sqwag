# Create your views here.
from django.shortcuts import render_to_response

def index (request):
    if not request.user.is_authenticated():
        print "logged out"
        return render_to_response('index.html',{ 'loggedIn' : 0 })
    print "logged in"
    return render_to_response('index.html',{ 'loggedIn' : 1 })
