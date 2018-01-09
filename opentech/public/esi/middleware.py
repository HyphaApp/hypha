from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed


class ESIMiddleware:
    """
    Adds "X-ESI: 1" header into the response if and ESI include has been used
    """
    def __init__(self, get_response):
        if not settings.ESI_ENABLED:
            raise MiddlewareNotUsed
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if getattr(request, '_esi_include_used', False):
            response['X-ESI'] = '1'

        return response
