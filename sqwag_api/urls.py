from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('sqwag_api.views',
    # Examples:
    url(r'^$', 'index', name='index'),
    url(r'^login/$', 'loginUser', name='login'),
    url(r'^register/$', 'registerUser', name='register'),
    url(r'^reqinvite/$', 'requestInvitation', name='req_invite'),
    url(r'^cronmail/$', 'cronMail', name='cron_email'),
    url(r'^activate/(?P<id>\d+)/(?P<key>\w+)$', 'activateUser', name='activate_user'),
    
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
