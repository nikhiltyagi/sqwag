from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import datetime
import random
import re
import sha

SHA1_RE = re.compile('^[a-f0-9]{40}$')

class UserAccount(models.Model):
    user = models.ForeignKey(User)
    account = models.CharField(max_length=200)
    account_id = models.CharField(max_length=100)
    access_token = models.CharField(max_length=4000)
    date_created = models.IntegerField()
    account_data = models.TextField(null=True)
    account_pic = models.URLField(null=True)
    account_handle = models.CharField(max_length=200, null=True)
    
    def __unicode__(self):
        return self.account

class UserProfile(models.Model):
    user =  models.OneToOneField(User)
    sqwag_image_url = models.URLField(null=True)
    sqwag_count = models.IntegerField()
    following_count = models.IntegerField()
    followed_by_count = models.IntegerField()
    pwd_reset_key = models.CharField(_('activation key'), max_length=40, null=True)
    displayname = models.CharField(_('displayname'), max_length=30)
    def create_reset_key(self, userProfile):
        salt = sha.new(str(random.random())).hexdigest()[:5]
        activation_key = sha.new(salt+userProfile.user.username).hexdigest()
        userProfile.pwd_reset_key = activation_key
        userProfile.save
        return activation_key

class Square(models.Model):
    user = models.ForeignKey(User)
    content_src = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    content_data = models.CharField(max_length=4000)
    content_description = models.CharField(max_length=4000,null=True)
    date_created = models.IntegerField('date published',null=True)
    shared_count = models.IntegerField(null=True)
    liked_count = models.IntegerField(null=True)
    user_account = models.ForeignKey(UserAccount, null=True)

    def __unicode__(self):
        return self.content_data

class UserSquare(models.Model):
    user = models.ForeignKey(User)
    square = models.ForeignKey(Square)
    date_shared = models.IntegerField('date shared')

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
