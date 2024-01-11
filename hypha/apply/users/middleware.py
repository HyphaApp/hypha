import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.log import log_response
from django.utils.translation import gettext_lazy as _
from social_core.exceptions import AuthForbidden
from social_django.middleware import (
    SocialAuthExceptionMiddleware as _SocialAuthExceptionMiddleware,
)

from hypha.apply.users.views import mfa_failure_view

logger = logging.getLogger("django.security.two_factor")

TWO_FACTOR_EXEMPTED_PATH_PREFIXES = [
    "/auth/",
    "/login/",
    "/logout/",
    "/account/",
    "/apply/submissions/success/",
]


def get_page_path(wagtail_page):
    _, _, page_path = wagtail_page.get_url_parts()
    return page_path


class SocialAuthExceptionMiddleware(_SocialAuthExceptionMiddleware):
    """
    Wrapper around SocialAuthExceptionMiddleware to customise messages
    """

    def get_message(self, request, exception):
        if isinstance(exception, AuthForbidden):
            return "Your credentials are not recognised."

        super().get_message(request, exception)


class TwoFactorAuthenticationMiddleware:
    """
    Middleware to enforce 2FA activation for unverified users

    To activate this middleware set env variable ENFORCE_TWO_FACTOR as True.

    This will redirect all request from unverified users to enable 2FA first.
    Except the request made on the url paths listed in TWO_FACTOR_EXEMPTED_PATH_PREFIXES.
    """

    reason = _("Two factor authentication required")

    def __init__(self, get_response):
        if not settings.ENFORCE_TWO_FACTOR:
            raise MiddlewareNotUsed()

        self.get_response = get_response

    def _accept(self, request):
        return self.get_response(request)

    def _reject(self, request, reason):
        response = mfa_failure_view(request, reason=reason)
        log_response(
            "Forbidden (%s): %s",
            reason,
            request.path,
            response=response,
            request=request,
            logger=logger,
        )
        return response

    def whitelisted_paths(self, path):
        if path == "/":
            return True

        for sub_path in TWO_FACTOR_EXEMPTED_PATH_PREFIXES:
            if path.startswith(sub_path):
                return True
        return False

    def get_urls_open_rounds(self):
        from hypha.apply.funds.models import ApplicationBase

        return map(
            get_page_path, ApplicationBase.objects.order_by_end_date().specific()
        )

    def get_urls_open_labs(self):
        from hypha.apply.funds.models import LabBase

        return map(
            get_page_path,
            LabBase.objects.public().live().specific(),
        )

    def __call__(self, request):
        if self.whitelisted_paths(request.path):
            return self._accept(request)

        # code to execute before the view
        user = request.user
        if user.is_authenticated:
            if user.social_auth.exists() or user.is_verified():
                return self._accept(request)

            # Allow rounds and lab detail pages
            if request.path in self.get_urls_open_rounds():
                return self._accept(request)

            if request.path in self.get_urls_open_labs():
                return self._accept(request)

            return self._reject(request, self.reason)

        return self._accept(request)
