from django.http import HttpResponsePermanentRedirect, Http404
from opentech.apply.home.models import ApplyHomePage
from opentech.reset_network.reset_network_home.models import ResetNetworkHomePage


# if we are on the root of the apply site (assuming an instance of the ApplyHomePage is set as the root page)
# redirect to the reset network home page
def redirect_apply_homepage_middleware(get_response):
    def middleware(request):
        try:
            current_url = '{scheme}://{host}{path}'.format(scheme=request.scheme, host=request.get_host(),
                                                           path=request.path)
            current_root_page = request.site.root_page.specific
            if isinstance(current_root_page, ApplyHomePage) and current_url == current_root_page.get_full_url():
                return HttpResponsePermanentRedirect(ResetNetworkHomePage.objects.first().get_url())
        except Exception as e:
            print(e)
            raise Http404()

        response = get_response(request)
        return response

    return middleware
