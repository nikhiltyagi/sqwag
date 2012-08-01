from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.forms import ModelForm
from sqwag_api.models import *


class RegisterationForm(forms.Form):
    fullname = forms.CharField(max_length=50,required=True)
    password = forms.CharField(max_length=128,required=True)
    #first_name = forms.CharField(max_length=30, required=False)
    #last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            #username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email):
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

class CreateCommentsForm(ModelForm):
    class Meta:
        model = SquareComments
        fields = ['user','square','comment']

class PwdResetForm(ModelForm):
    class Meta:
        model = User
        fields = ['id','password']

class EditEmailForm(forms.Form):
    email = forms.EmailField()
    oldPassword = forms.CharField(max_length=128)
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        if email:
            try:
                email_name, domain_part = email.strip().split('@', 1)
            except ValueError:
                pass
            else:
                email = '@'.join([email_name, domain_part.lower()])
            username = self.cleaned_data.get('username')
            if email and User.objects.filter(email=email).exclude(username=username).count():
                raise forms.ValidationError(u'Email addresses must be unique.')
            return email
        else:
            raise forms.ValidationError(u'Email is a required field')

class EditDisplayName(forms.Form):
    displayName = forms.CharField(max_length=30)    

class ChangePasswordForm(forms.Form):
    newPassword = forms.CharField(max_length=128)
    oldPassword = forms.CharField(max_length=128)

class ContentDescriptionForm(forms.Form):
    content_desc = forms.CharField(max_length=4000,required=False)   
    
class ChangeUserNameForm(forms.Form):
    password = forms.CharField(max_length=128) 
    username = forms.CharField(max_length=30)
    def validateUserName(self):
        username = self.cleaned_data.get('username')
        if username:
            if username and UserProfile.objects.filter(username=username).count():
                raise forms.ValidationError(u'username must be unique.')
            return username
        else:
            raise forms.ValidationError(u'Username is required')

class FeedbackForm(forms.Form):
    feedback = forms.CharField(max_length=4000)

class SendSqwagForm(forms.Form):
    username = forms.CharField(max_length=30)
    userSquare = forms.IntegerField()
    message = forms.CharField(max_length=2000,required=False)

class forgotPwdForm(forms.Form):
    username = forms.CharField(max_length=100)