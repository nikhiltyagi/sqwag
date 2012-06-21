from django.http import HttpResponse
from piston.resource import Resource
from piston.handler import AnonymousBaseHandler, BaseHandler

class CORSResource(Resource):
    """
    Piston Resource to enable CORS.
    """

    # headers sent in all responses
    cors_headers = [
        ('Access-Control-Allow-Origin',     '*'),
        ('Access-Control-Allow-Headers',    'Authorization'),
    ]

    # headers sent in pre-flight responses
    preflight_headers = cors_headers + [
        ('Access-Control-Allow-Methods',    'GET'),
        ('Access-Control-Allow-Credentials','true')
    ]

    def __call__(self, request, *args, **kwargs):

        request_method = request.method.upper()

        # intercept OPTIONS method requests
        if request_method == "OPTIONS":
            # preflight requests don't need a body, just headers
            resp = HttpResponse()

            # add headers to the empty response
            for hk, hv in self.preflight_headers:
                resp[hk] = hv

        else:
            # otherwise, behave as if we called  the base Resource
            resp = super(CORSResource, self).__call__(request, *args, **kwargs)

            # slip in the headers after we get the response
            # from the handler
            for hk, hv in self.cors_headers:
                resp[hk] = hv

        return resp