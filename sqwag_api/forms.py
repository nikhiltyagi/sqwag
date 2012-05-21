from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm
from sqwag_api.models import *


class RegisterationForm(ModelForm):
    class Meta:
        model = User
        fields = ['username','password','first_name','last_name','email']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(username=username).count():
                raise forms.ValidationError(u'Email addresses must be unique.')
            return email
        else:
            raise forms.ValidationError(u'Email is a required field')

class CreateSquareForm(ModelForm):
    class Meta:
        model = Square
        fields = ['id','content_src','content_type','content_data']

class CreateImageSquareForm(ModelForm):
    class Meta:
        model = Square
        fields = ['id','content_src','content_type']

class RequestInvitationForm(ModelForm):
    class Meta:
        model =  RequestInvitation
        fields = ['email']
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            x="test"
#            if email and RequestInvitation.objects.filter(email=email).count():
#                raise forms.ValidationError(u'We have already received your request earlier, Thank you for your interest.')
            return email
        else:
            raise forms.ValidationError(u'Email is a required field')

class CreateRelationshipForm(ModelForm):
    class Meta:
        model = Relationship
        fields = ['id','subscriber','producer']