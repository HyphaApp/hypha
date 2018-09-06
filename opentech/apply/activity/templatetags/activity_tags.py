from django import template

from opentech.apply.determinations.models import Determination
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


@register.filter
def user_can_see_related(activity, user):
    if not activity.related_object:
        return False

    if user.is_apply_staff:
        return True

    if isinstance(activity.related_object, Determination):
        return True

    return False
