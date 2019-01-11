import json

from django import template

from opentech.apply.determinations.models import Determination
from opentech.apply.review.models import Review

from ..models import VISIBILITY

register = template.Library()


@register.filter
def display_author(activity, user):
    if user.is_applicant and isinstance(activity.related_object, Review):
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


@register.filter
def display_for(activity, user):
    try:
        message_data = json.loads(activity.message)
    except json.JSONDecodeError:
        return activity.message

    visibile_for_user = activity.visibility_for(user)

    visible_messages = len(set(visibile_for_user) & set(message_data))

    if visible_messages == 1:
        base_template = '{message}'
    else:
        base_template = '<p>{visibility}: {message}</p>'

    return ''.join(
        base_template.format(visibility=VISIBILITY.get(visibility), message=message)
        for visibility, message in message_data.items()
        if visibility in visibile_for_user
    )
