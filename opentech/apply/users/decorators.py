from django.conf import settings
from django.core.exceptions import PermissionDenied


def require_oauth_whitelist(view_func):
    """Simple decorator that limits the use of OAuth to the configure whitelisted domains"""
    def decorated_view(request, *args, **kwargs):
        user = request.user

        try:
            if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS:
                for domain in settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS:
                    if user.email.endswith(f'@{domain}'):
                        return view_func(request, *args, **kwargs)
        except AttributeError:
            raise PermissionDenied

        raise PermissionDenied

    return decorated_view
