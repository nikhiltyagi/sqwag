from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('sqwag_api.views',
    # Examples:
    url(r'^$', 'index', name='index'),
    url(r'^logout/$', 'logoutUser', name='logout'),
    url(r'^login/$', 'loginUser', name='login'),
    url(r'^register/$', 'registerUser', name='register'),
    url(r'^reqinvite/$', 'requestInvitation', name='req_invite'),
    url(r'^cronmail/$', 'cronMail', name='cron_email'),
    url(r'^activate/(?P<id>\d+)/(?P<key>\w+)$', 'activateUser', name='activate_user'),
    url(r'^authtwitter/$', 'authTwitter', name='authtwitter'),
    url(r'^accesstweeter/$', 'accessTweeter', name='accesstwitter'),
    url(r'^synctwitterfeeds/$', 'syncTwitterFeeds', name='synctwiter'),
    url(r'^authinsta/$', 'authInsta', name='authinsta'),
    url(r'^accessinsta/$', 'accessInsta', name='accessinsta'),
    url(r'^authfacebook/$','authFacebook',name='authFacebook'),
    url(r'^accessfacebook/$','accessFacebook',name='accessFacebook'),
    url(r'^authfacebooknewuser/$','authFacebookNewUser',name='authFacebookNewUser'),
    url(r'^accessfacebooknewuser/$','accessFacebookNewUser',name='accessFacebookNewUser'),
    url(r'^retweet/(?P<square_id>\d+)$', 'retweet',name='retweet'),
    url(r'^replytweet/(?P<square_id>\d+)/(?P<message>\w+)/(?P<user_handle>\w+)$','replyTweet',name='replyTweet'),
    url(r'^favouritetweet/(?P<square_id>\d+)/$','favTweet',name='favTweet'),
    url(r'^tweet/(?P<message>\w+)/$','postTweet',name='postTweet'),
    url(r'^getinstafeed$','getInstaFeed',name='getInstaFeed'),
    url(r'^forgotpwd/$','forgotPwd',name='forgotPwd'),
    url(r'^pwdreset/(?P<id>\d+)/(?P<key>\w+)$','forgotPwdKey',name='forgotPwdKey'),
    url(r'^newpwd/$','newPwd',name='newPwd'),
    url(r'^editEmail/$','editEmail',name='editEmail'),
    url(r'^editDisplayName/$','editDisplayName',name='editDisplayName'),
    url(r'^changePassword/$','changePassword',name='changePassword'),
    url(r'^changeUserName/$','changeUserName',name='changeUserName'),
    url(r'^test/$','GetElasticSearch',name='GetElasticSearch'),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
