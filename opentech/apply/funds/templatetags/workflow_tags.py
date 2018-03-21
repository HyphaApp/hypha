from django import template

register = template.Library()


def check_permission(user, perm, submission):
    return submission.phase.has_perm(user, perm)


@register.filter
def has_edit_perm(user, submission):
    return check_permission(user, 'edit', submission)


@register.filter
def has_review_perm(user, submission):
    return check_permission(user, 'review', submission)
