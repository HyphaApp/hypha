"""
elevate.views
~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:copyright: (c) 2014-2016 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

from urllib.parse import urlparse, urlunparse

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import resolve_url
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.utils.module_loading import import_string
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import View

from .forms import ElevateForm
from .settings import (
    REDIRECT_FIELD_NAME,
    REDIRECT_TO_FIELD_NAME,
    REDIRECT_URL,
    URL,
)
from .utils import grant_elevated_privileges

try:
    from django.utils.http import url_has_allowed_host_and_scheme
except ImportError:
    # Remove once Django 2.2 is EOL
    from django.utils.http import is_safe_url as url_has_allowed_host_and_scheme


class ElevateView(View):
    """
    The default view for the Elevate mode page. The role of this page is to
    prompt the user for their password again, and if successful, redirect
    them back to ``next``.
    """

    form_class = ElevateForm
    template_name = "elevate/elevate.html"
    extra_context = None

    def handle_elevate(self, request, redirect_to, context):
        return request.method == "POST" and context["form"].is_valid()

    def grant_elevated_privileges(self, request, redirect_to):
        grant_elevated_privileges(request)
        # Restore the redirect destination from the GET request
        redirect_to = request.session.pop(REDIRECT_TO_FIELD_NAME, redirect_to)
        # Double check we're not redirecting to other sites
        if not url_has_allowed_host_and_scheme(
            redirect_to,
            allowed_hosts=[request.get_host()],
            require_https=request.is_secure(),
        ):
            redirect_to = resolve_url(REDIRECT_URL)
        return HttpResponseRedirect(redirect_to)

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, request):
        redirect_to = request.GET.get(REDIRECT_FIELD_NAME, REDIRECT_URL)

        # Make sure we're not redirecting to other sites
        if not url_has_allowed_host_and_scheme(
            redirect_to,
            allowed_hosts=[request.get_host()],
            require_https=request.is_secure(),
        ):
            redirect_to = resolve_url(REDIRECT_URL)

        if request.is_elevated():
            return HttpResponseRedirect(redirect_to)

        if request.method == "GET":
            request.session[REDIRECT_TO_FIELD_NAME] = redirect_to

        context = {
            "form": self.form_class(request, request.user, request.POST or None),
            "request": request,
            REDIRECT_FIELD_NAME: redirect_to,
        }
        if self.handle_elevate(request, redirect_to, context):
            return self.grant_elevated_privileges(request, redirect_to)
        if self.extra_context is not None:
            context.update(self.extra_context)
        return TemplateResponse(request, self.template_name, context)


def elevate(request, **kwargs):
    return ElevateView(**kwargs).dispatch(request)


def redirect_to_elevate(next_url, elevate_url=None):
    """
    Redirects the user to the login page, passing the given 'next' page
    """
    if elevate_url is None:
        elevate_url = URL

    try:
        # django 1.10 and greater can't resolve the string 'elevate.views.elevate' to a URL
        # https://docs.djangoproject.com/en/1.10/releases/1.10/#removed-features-1-10
        elevate_url = import_string(elevate_url)
    except ImportError:
        pass  # wasn't a dotted path

    elevate_url_parts = list(urlparse(resolve_url(elevate_url)))

    querystring = QueryDict(elevate_url_parts[4], mutable=True)
    querystring[REDIRECT_FIELD_NAME] = next_url
    elevate_url_parts[4] = querystring.urlencode(safe="/")

    return HttpResponseRedirect(urlunparse(elevate_url_parts))
