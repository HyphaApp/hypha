from django.core.exceptions import PermissionDenied

from .utils import can_use_oauth_check


def require_oauth_whitelist(view_func):
    """Simple decorator that limits the use of OAuth to the configure whitelisted domains"""
    def decorated_view(request, *args, **kwargs):
        if can_use_oauth_check(request.user):
            return view_func(request, *args, **kwargs)

        raise PermissionDenied

    return decorated_view
