from django.conf.urls.defaults import patterns, include, url
import settings
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^sqwag/', include('sqwag.sqwag_api.urls')),
    url(r'^api/', include('sqwag.api.urls')),
    url(r'^assets/(?P<path>.*)$', 'django.views.static.serve',{'document_root': settings.CONTENT_BASE}),
    url(r'^', include('sqwag.sqwag_frontend.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

