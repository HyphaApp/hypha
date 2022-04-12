from django.conf import settings
from django.shortcuts import redirect
from social_core.exceptions import AuthForbidden
from social_django.middleware import (
    SocialAuthExceptionMiddleware as _SocialAuthExceptionMiddleware,
)


class SocialAuthExceptionMiddleware(_SocialAuthExceptionMiddleware):
    """
    Wrapper around SocialAuthExceptionMiddleware to customise messages
    """
    def get_message(self, request, exception):
        if isinstance(exception, AuthForbidden):
            return 'Your credentials are not recognised.'

        super().get_message(request, exception)


class TwoFactorAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def is_path_allowed(self, path):
        allowed_urls = [
            'login/',
            'logout/',
            'account/',
            'two_factor/',
        ]
        for url in allowed_urls:
            if url in path:
                return True
        return False

    def __call__(self, request):
        # code to execute before the view
        user = request.user
        if settings.ENFORCE_TWO_FACTOR and user.is_authenticated and not user.is_verified() and not self.is_path_allowed(request.path):
            return redirect('/account/two_factor/required/')

        response = self.get_response(request)

        # code to execute after view
        return response
