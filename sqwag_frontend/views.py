# Create your views here.
from django.shortcuts import render_to_response
from django.template.context import Context
from sqwag_api.helper import getCompleteUserInfo

def index (request):
    if not request.user.is_authenticated():
        print "logged out"
        return render_to_response('index.html')
    print "logged in"
    user_image_url = None
    complete_user = getCompleteUserInfo(request,request.user)
    if complete_user['status']==1:
        complete_user = complete_user['result']
        user_profile = complete_user['user_profile']
        if user_profile['sqwag_image_url']:
            user_image_url = complete_user['user_profile']['sqwag_image_url']
        elif complete_user['user_accounts']:
            for user_account in complete_user['user_accounts']:
                if user_account['account_pic']:
                    user_image_url = user_account['account_pic']
                    break
        else:
            user_image_url = "http://graph.facebook.com/apnerve/picture/"
    c = Context({
        'complete_user': complete_user,
        'user_image_url': user_image_url,
    })
    return render_to_response('index.html',c)
