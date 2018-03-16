from django import template

register = template.Library()


@register.filter()
def can_edit(user, submission):
    return submission.phase.has_perm(user, 'edit')
