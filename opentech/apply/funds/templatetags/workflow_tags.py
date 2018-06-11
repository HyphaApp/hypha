from django import template

register = template.Library()


def check_permission(user, perm, submission):
    perm_method = getattr(submission.phase['permissions'], f'can_{perm}', lambda x: False)
    return perm_method(user)


@register.filter
def has_edit_perm(user, submission):
    return check_permission(user, 'edit', submission)


@register.filter
def has_review_perm(user, submission):
    return check_permission(user, 'review', submission)
