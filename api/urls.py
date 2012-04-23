from django.conf.urls.defaults import *
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication

from api.handlers import *

#auth = HttpBasicAuthentication(realm="sqwag")
#ad = { 'authentication': auth }

square_resource = Resource(handler=SquareHandler)#, **ad)
user_self_feeds_resource =  Resource(handler=UserSelfFeedsHandler)
#arbitrary_resource = Resource(handler=ArbitraryDataHandler)#, **ad)

urlpatterns = patterns('',
    url(r'^square/(?P<id>\d+)$', square_resource,{ 'emitter_format': 'json' }),
    url(r'^user/feeds/(?P<user_id>\d+)$', user_self_feeds_resource,{ 'emitter_format': 'json' }),
    url(r'^square', square_resource,{ 'emitter_format': 'json' }),
)