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
square_delete_resource = CORSResource(handler=DeleteSquareHandler)
top_sqwags_resource = CORSResource(handler=TopSqwagsFeedsHandler)
public_sqwags_resource = CORSResource(handler=PublicSqwagsFeedsHandler)
userinfo_resource = CORSResource(handler=UserInfo)
image_square_resource = CORSResource(handler=ImageSquareHandler)#, **ad)
square_comments_resource = CORSResource(handler=CommentsSquareHandler)

#arbitrary_resource = Resource(handler=ArbitraryDataHandler)#, **ad)

urlpatterns = patterns('',
    url(r'^square/(?P<id>\d+)$', square_resource,{ 'emitter_format': 'json' }),
    url(r'^user/feeds/(?P<page>\d+)$', user_self_feeds_resource,{ 'emitter_format': 'json' }),
    url(r'^square/create', square_resource,{ 'emitter_format': 'json' }),
    url(r'^square/share', share_square_resource,{ 'emitter_format': 'json' }),
    url(r'^subscribe/', relationship_resource,{ 'emitter_format': 'json' }),
    url(r'^user/homefeeds/(?P<page>\d+)$', home_page_feeds_resource,{ 'emitter_format': 'json' }),
    url(r'^user/homefeeds/', home_page_feeds_resource,{ 'emitter_format': 'json' }),
    url(r'^square/delete', square_delete_resource,{'emitter_format': 'json'}),
    url(r'^user/topsqwagsfeeds/(?P<page>\d+)$', top_sqwags_resource,{ 'emitter_format': 'json' }),
    url(r'^user/topsqwagsfeeds/', top_sqwags_resource,{ 'emitter_format': 'json' }),
    url(r'^publicsqwagfeed/(?P<page>\d+)$', public_sqwags_resource,{ 'emitter_format': 'json' }),
    url(r'^userinfo/(?P<id>\d+)$',userinfo_resource,{'emitter_format': 'json'}),
    url(r'^userinfo/',userinfo_resource,{'emitter_format': 'json'}),
    url(r'^imagesquare/create', image_square_resource, {'emitter_format': 'json'}),
    url(r'^square/getcomments/(?P<id>\d+)',square_comments_resource,{'emitter_format':'json'}),
    url(r'^square/postcomments',square_comments_resource,{'emitter_format':'json'}),
)
