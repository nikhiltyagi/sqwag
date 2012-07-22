from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import datetime
import random
import re
import sha
import os
from django_facebook import model_managers
from django_facebook.models import *
from django_facebook.views import *

SHA1_RE = re.compile('^[a-f0-9]{40}$')
PROFILE_IMAGE_PATH = os.path.join('images','facebook_profiles/%Y/%m/%d')

class UserAccount(models.Model):
    user = models.ForeignKey(User)
    account = models.CharField(max_length=200)
    account_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=4000)
    date_created = models.IntegerField()
    account_data = models.TextField(null=True)
    account_pic = models.URLField(null=True)
    account_handle = models.CharField(max_length=200, null=True)
    is_active = models.BooleanField(default=True)
    
    def __unicode__(self):
        return self.account

class UserProfile(models.Model):
    user =  models.OneToOneField(User)
    username = models.CharField(_('username'), max_length=100, unique=True,null=True)
    sqwag_image_url = models.URLField(null=True)
    sqwag_cover_image_url = models.URLField(null=True)
    personal_message = models.TextField(null=True)
    sqwag_count = models.IntegerField()
    following_count = models.IntegerField()
    followed_by_count = models.IntegerField()
    pwd_reset_key = models.CharField(_('activation key'), max_length=40, null=True)
    displayname = models.CharField(_('displayname'), max_length=30)
    fullname = models.CharField(max_length=30)
    def create_reset_key(self, userProfile):
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+userProfile.user.username).hexdigest()
        userProfile.pwd_reset_key = activation_key
        userProfile.save
        return activation_key

class Square(models.Model):
    user = models.ForeignKey(User)
    content_id = models.CharField(max_length=400, null=True)
    content_src = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    content_data = models.CharField(max_length=4000)
    content_description = models.CharField(max_length=4000,null=True)
    date_created = models.IntegerField('date published',null=True)
    shared_count = models.IntegerField(null=True)
    is_deleted = models.BooleanField(default=False)
    user_account = models.ForeignKey(UserAccount, null=True)

    def __unicode__(self):
        return self.content_data

class UserSquare(models.Model):
    user = models.ForeignKey(User)
    square = models.ForeignKey(Square)
    date_shared = models.IntegerField('date shared')
    is_deleted = models.BooleanField(default=False)
    content_description = models.CharField(max_length=4000,null=True)
    is_owner = models.BooleanField()
    is_private = models.BooleanField(default=False)
        
    def __unicode__(self):
        return self.date_shared

class RequestInvitation(models.Model):
    email = models.EmailField(max_length=254)
    date_requested = models.IntegerField('date requested')
    
    def __unicode__(self):
        return self.email

class Emailer(models.Model):
    to = models.EmailField(max_length=254,null=False)
    from_email = models.EmailField(max_length=254, null=False)
    body = models.TextField()
    subject = models.CharField(max_length=100)
    date_created = models.IntegerField()
    is_sent = models.BooleanField(default=False)
    status = models.TextField(null=True)

class Relationship(models.Model):
    subscriber = models.ForeignKey(User,related_name='subscriber')
    producer = models.ForeignKey(User, related_name='producer')
    date_subscribed = models.IntegerField('date subscribed')
    permission = models.BooleanField()
    
#    def __unicode__(self):
#        return self.date_subscribed

class RegistrationManager(models.Manager):
    def activate_user(self, activation_key):
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = "ALREADY_ACTIVATED"
                profile.save()
                return user
        return False

    def create_profile(self, user):
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+user.username).hexdigest()
        return self.create(user=user,
                           activation_key=activation_key)
        
    def delete_expired_users(self):
        for profile in self.all():
            if profile.activation_key_expired():
                user = profile.user
                if not user.is_active:
                    user.delete()


class RegistrationProfile(models.Model):
    user = models.ForeignKey(User, unique=True, verbose_name=_('user'))
    activation_key = models.CharField(_('activation key'), max_length=40)
    date_activated = models.IntegerField('date activated',null=True)
    is_deleted = models.BooleanField('active',default=False)
    
    objects = RegistrationManager()
    
    class Meta:
        verbose_name = _('registration profile')
        verbose_name_plural = _('registration profiles')
    
    def __unicode__(self):
        return u"Registration information for %s" % self.user
    
    def activation_key_expired(self):
        expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == "ALREADY_ACTIVATED" or \
               (self.user.date_joined + expiration_date <= datetime.datetime.now())
    activation_key_expired.boolean = True	


class SyncTwitterFeed(models.Model):
    last_tweet = models.CharField(max_length=40)
    date_created = models.IntegerField()
    last_sync_time = models.IntegerField()
    def __unicode__(self):
        return self.last_tweet

class SquareComments(models.Model):
    user = models.ForeignKey(User,related_name='user')
    square = models.ForeignKey(Square,related_name='square')
    date_created = models.IntegerField()
    comment = models.CharField(max_length=4000,null=False)

class Feedback(models.Model):
    user = models.ForeignKey(User, null=True)
    date_created = models.IntegerField()
    feedback = models.TextField()
    
class Notifications(models.Model):
    user = models.ForeignKey(User,related_name='recievinguser')
    date_created = models.IntegerField()
    userSquare = models.ForeignKey(UserSquare)
    sendingUser = models.ForeignKey(User,related_name='sendingUser')
    is_seen = models.BooleanField(default=False)
    notification_type = models.CharField(max_length=100)
    notification_message = models.CharField(max_length=4000,null=True)

class PrivateSquare(models.Model):
    user = models.ForeignKey(User,related_name='recieving_user')
    userSquare = models.ForeignKey(UserSquare,related_name='shared_square')
    
class FacebookProfileModel(models.Model):
    '''
    Abstract class to add to your profile model.
    NOTE: If you don't use this this abstract class, make sure you copy/paste
    the fields in.
    '''
    about_me = models.TextField(blank=True)
    facebook_id = models.BigIntegerField(blank=True, unique=True, null=True)
    access_token = models.TextField(
        blank=True, help_text='Facebook token for offline access')
    facebook_name = models.CharField(max_length=255, blank=True)
    facebook_profile_url = models.TextField(blank=True)
    website_url = models.TextField(blank=True)
    blog_url = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True,upload_to=PROFILE_IMAGE_PATH, max_length=255)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=(('m', 'Male'), ('f', 'Female')), blank=True, null=True)
    raw_data = models.TextField(blank=True)

    def __unicode__(self):
        return self.user.__unicode__()

    class Meta:
        abstract = True
        
    def likes(self):
        likes = FacebookLike.objects.filter(user_id=self.user_id)
        return likes
    
    def friends(self):
        friends = FacebookUser.objects.filter(user_id=self.user_id)
        return friends

    def post_facebook_registration(self, request):
        '''
        Behaviour after registering with facebook
        '''
        from django_facebook.utils import next_redirect
        default_url = reverse('facebook_connect')
        response = next_redirect(request, default=default_url,
                                 next_key='register_next')
        response.set_cookie('fresh_registration', self.user_id)

        return response
    
    def clear_access_token(self):
        self.access_token = None
        self.save()

    def get_offline_graph(self):
        '''
        Returns a open facebook graph client based on the access token stored
        in the user's profile
        '''
        from open_facebook.api import OpenFacebook
        if self.access_token:
            graph = OpenFacebook(access_token=self.access_token)
            graph.current_user_id = self.facebook_id
            return graph
    
