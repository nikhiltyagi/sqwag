from api.cors_resource import CORSResource
from api.handlers import *
from django.conf.urls.defaults import *
from piston.authentication import HttpBasicAuthentication
from piston.resource import Resource


#auth = HttpBasicAuthentication(realm="sqwag")
#ad = { 'authentication': auth }

square_resource = CORSResource(handler=SquareHandler)#, **ad)
user_self_feeds_resource =  CORSResource(handler=UserSelfFeedsHandler)
share_square_resource = CORSResource(handler=ShareSquareHandler)
relationship_resource = CORSResource(handler=RelationshipHandler)
home_page_feeds_resource = CORSResource(handler=HomePageFeedHandler)
#arbitrary_resource = Resource(handler=ArbitraryDataHandler)#, **ad)

urlpatterns = patterns('',
    url(r'^square/(?P<id>\d+)$', square_resource,{ 'emitter_format': 'json' }),
    url(r'^user/feeds/(?P<user_id>\d+)$', user_self_feeds_resource,{ 'emitter_format': 'json' }),
    url(r'^square/create', square_resource,{ 'emitter_format': 'json' }),
    url(r'^square/share', share_square_resource,{ 'emitter_format': 'json' }),
    url(r'^subscribe/', relationship_resource,{ 'emitter_format': 'json' }),
    url(r'^user/homefeeds/(?P<user_id>\d+)$', home_page_feeds_resource,{ 'emitter_format': 'json' }),
)