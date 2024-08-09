from django import template
from django.conf import settings

register = template.Library()


def check_permission(user, perm, submission):
    if submission.is_archive:
        return False
    perm_method = getattr(submission.phase.permissions, f"can_{perm}", lambda x: False)
    return perm_method(user)


@register.filter
def has_edit_perm(user, submission):
    return check_permission(user, "edit", submission)


@register.filter
def has_review_perm(user, submission):
    return check_permission(user, "review", submission)


@register.filter
def has_withdraw_perm(user, submission):
    if settings.ENABLE_SUBMISSION_WITHDRAWAL:
        return check_permission(user, "withdraw", submission)
    return False
