from django.conf.urls.defaults import *

urlpatterns = patterns('',
	(r'^$', 'django_openid_consumer.views.begin'),
    (r'^complete/$', 'django_openid_consumer.views.complete'),
    (r'^signout/$', 'django_openid_consumer.views.signout'),
)
