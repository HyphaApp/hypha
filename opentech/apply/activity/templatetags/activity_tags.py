from django import template

register = template.Library()


@register.filter
def display_author(activity, user):
    if user.is_applicant:
        return None
    return activity.user
