import logging

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.urls import set_urlconf
from django.utils.log import log_response
from django.utils.translation import gettext_lazy as _
from social_core.exceptions import AuthForbidden
from social_django.middleware import (
    SocialAuthExceptionMiddleware as _SocialAuthExceptionMiddleware,
)

from hypha.apply.users.views import mfa_failure_view

ALLOWED_SUBPATH_FOR_UNVERIFIED_USERS = [
    "/auth/",
    "/login/",
    "/logout/",
    "/account/",
]

logger = logging.getLogger("django.security.mfa")


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
    Except the request made on the url paths listed in ALLOWED_SUBPATH_FOR_UNVERIFIED_USERS.
    """

    reason = _("Two factor authentication required")

    def __init__(self, get_response):
        if not settings.ENFORCE_TWO_FACTOR:
            raise MiddlewareNotUsed()

        self.get_response = get_response

    def _accept(self, request):
        return self.get_response(request)

    def _reject(self, request, reason):
        set_urlconf("hypha.apply.urls")
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

    def is_path_allowed(self, path):
        if path == "/":
            return True
        for sub_path in ALLOWED_SUBPATH_FOR_UNVERIFIED_USERS:
            if path.startswith(sub_path):
                return True
        return False

    def __call__(self, request):
        if self.is_path_allowed(request.path):
            return self._accept(request)

        # code to execute before the view
        user = request.user
        if user.is_authenticated:
            if user.social_auth.exists() or user.is_verified():
                return self._accept(request)

            return self._reject(request, self.reason)

        return self._accept(request)
