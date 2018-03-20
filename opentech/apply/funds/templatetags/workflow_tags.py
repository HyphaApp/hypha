from django import template

register = template.Library()


def check_permission(user, perm, submission):
    return submission.phase.has_perm(user, perm)


@register.filter
def can_edit(user, submission):
    return check_permission(user, 'edit', submission)


@register.filter
def can_review(user, submission):
    return check_permission(user, 'review', submission)
