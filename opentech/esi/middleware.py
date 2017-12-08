class ESIMiddleware:
    """
    Adds "X-ESI: 1" header into the response if and ESI include has been used
    """

    def process_response(self, request, response):
        if getattr(request, '_esi_include_used', False):
            response['X-ESI'] = '1'

        return response
