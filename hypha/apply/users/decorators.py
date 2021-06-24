from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied

from .utils import can_use_oauth_check


def require_oauth_whitelist(view_func):
    """Simple decorator that limits the use of OAuth to the configure whitelisted domains"""
    def decorated_view(request, *args, **kwargs):
        if can_use_oauth_check(request.user):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return decorated_view


def is_apply_staff(user):
    if not user.is_apply_staff:
        raise PermissionDenied
    return True


def is_finance(user):
    if not user.is_finance:
        raise PermissionDenied
    return True


def is_apply_staff_or_finance(user):
    if not (user.is_apply_staff or user.is_finance):
        raise PermissionDenied
    return True


def is_approver(user):
    if not user.is_approver:
        raise PermissionDenied
    return True


staff_required = [login_required, user_passes_test(is_apply_staff)]

finance_required = [login_required, user_passes_test(is_finance)]

staff_or_finace_required = [login_required, user_passes_test(is_apply_staff_or_finance)]

approver_required = [login_required, user_passes_test(is_approver)]


def superuser_decorator(fn):
    check = user_passes_test(lambda user: user.is_superuser)
    return check(fn)
