from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from wagtail.models import Site

from .home.models import ApplyHomePage


class HandleProtectionErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def process_exception(self, request, exception):
        if isinstance(exception, ProtectedError):
            messages.error(
                request,
                _('The object you are trying to delete is used somewhere. Please remove any usages and try again!.'),
            )
            return HttpResponseRedirect(request.path)

        return None

    def __call__(self, request):
        response = self.get_response(request)
        return response


def apply_url_conf_middleware(get_response):
    # If we are on a page which belongs to the same site as an ApplyHomePage
    # we change the url conf to one that includes links to all the logged
    # in functionality. Login and Logout are included with the global package
    # of urls
    def middleware(request):
        site = Site.find_for_request(request)
        homepage = site.root_page.specific
        if isinstance(homepage, ApplyHomePage):
            request.urlconf = 'hypha.apply.urls'

        response = get_response(request)
        return response

    return middleware
