'''
Created on 15-Aug-2012

@author: saini
'''
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class FbCustomBackend(ModelBackend):
    def authenticate(self, username =None, password=None):
        try:
            user = User.objects.get(username=username)
            if user.is_active:
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
