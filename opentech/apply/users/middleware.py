from social_core.exceptions import AuthForbidden
from social_django.middleware import SocialAuthExceptionMiddleware as _SocialAuthExceptionMiddleware


class SocialAuthExceptionMiddleware(_SocialAuthExceptionMiddleware):
    """
    Wrapper around SocialAuthExceptionMiddleware to customise messages
    """
    def get_message(self, request, exception):
        if isinstance(exception, AuthForbidden):
            return 'Your credentials are not recognised.'

        super().get_message(request, exception)
