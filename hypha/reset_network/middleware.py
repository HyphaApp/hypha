from django.http import Http404, HttpResponsePermanentRedirect

from wagtail.core.models import Site

from hypha.apply.home.models import ApplyHomePage
from hypha.reset_network.reset_network_home.models import ResetNetworkHomePage


# if we are on the root of the apply site (assuming an instance of the ApplyHomePage is set as the root page)
# redirect to the reset network home page
def redirect_apply_homepage_middleware(get_response):
    def middleware(request):
        try:
            current_url = '{scheme}://{host}{path}'.format(scheme=request.scheme, host=request.get_host(),
                                                           path=request.path)
            site = Site.find_for_request(request)
            current_root_page = site.root_page.specific
            if isinstance(current_root_page, ApplyHomePage) and current_url == current_root_page.get_full_url():
                return HttpResponsePermanentRedirect(ResetNetworkHomePage.objects.first().get_url())
        except Exception as e:
            print(e)
            raise Http404()

        response = get_response(request)
        return response

    return middleware
