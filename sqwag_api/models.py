from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
import datetime
import random
import re
import sha

SHA1_RE = re.compile('^[a-f0-9]{40}$')

class Square(models.Model):
    user = models.ForeignKey(User)
    content_src = models.CharField(max_length=200)
    content_type = models.CharField(max_length=50)
    content_data = models.CharField(max_length=4000)
    content_description = models.CharField(max_length=4000,null=True)
    date_created = models.IntegerField('date published',null=True)
    shared_count = models.IntegerField(null=True)
    liked_count = models.IntegerField(null=True)

    def __unicode__(self):
        return self.content_data

class UserSquare(models.Model):
    user = models.ForeignKey(User)
    square = models.ForeignKey(Square)
    date_shared = models.IntegerField('date shared')

    def __unicode__(self):
        return self.date_shared

class UserAccount(models.Model):
    user = models.ForeignKey(User)
    account = models.CharField(max_length=200)
    account_id = models.CharField(max_length=100)

    def __unicode__(self):
        return self.account

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
    
#    def create_inactive_user(self, username, password, email,
#                             send_email=True, profile_callback=None):
#        new_user = User.objects.create_user(username, email, password)
#        new_user.is_active = False
#        new_user.save()
#        
#        registration_profile = self.create_profile(new_user)
#        
#        if profile_callback is not None:
#            profile_callback(user=new_user)
#        
#        if send_email:
#            from django.core.mail import send_mail
#            current_site = Site.objects.get_current()
#            
#            subject = render_to_string('registration/activation_email_subject.txt',
#                                       { 'site': current_site })
#            # Email subject *must not* contain newlines
#            subject = ''.join(subject.splitlines())
#            
#            message = render_to_string('registration/activation_email.txt',
#                                       { 'activation_key': registration_profile.activation_key,
#                                         'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
#                                         'site': current_site })
#            
#            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_user.email])
#        return new_user
    
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
