from django import template

from opentech.apply.review.models import Review

register = template.Library()


@register.filter
def display_author(activity, user):
    if (
        user.is_applicant and
        isinstance(activity.related_object, Review) and
        not activity.user.is_apply_staff
    ):
        return 'Reviewer'
    return activity.user
