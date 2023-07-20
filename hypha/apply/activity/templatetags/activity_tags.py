import json

from django import template
from django.conf import settings

from hypha.apply.determinations.models import Determination
from hypha.apply.projects.models import Contract
from hypha.apply.review.models import Review

from ..models import ALL, REVIEWER, TEAM

register = template.Library()


@register.filter
def display_author(activity, user):
    if isinstance(activity.related_object, Review) and activity.source.user == user:
        return 'Reviewer'
    return activity.user.get_full_name_with_group()


@register.filter
def user_can_see_related(activity, user):
    if not activity.related_object:
        return False

    if user.is_apply_staff:
        return True

    if isinstance(activity.related_object, (Determination, Contract)):
        return True

    return False


@register.filter
def display_for(activity, user):
    try:
        message_data = json.loads(activity.message)
    except json.JSONDecodeError:
        return activity.message
    else:
        # A message with only numbers (int) is valid json so check we have "real" json.
        if not isinstance(message_data, (dict, list)):
            return activity.message

    visibile_for_user = activity.visibility_for(user)

    if set(visibile_for_user) & {TEAM, REVIEWER}:
        return message_data[TEAM]

    return message_data[ALL]


@register.filter
def visibility_options(activity, user):
    choices = activity.visibility_choices_for(user)
    return json.dumps(choices)


@register.filter
def visibility_display(visibility, user):
    if not user.is_apply_staff and not user.is_finance and not user.is_contracting:
        return f"{visibility} + {settings.ORG_SHORT_NAME} team"
    if visibility != TEAM:
        return f"{visibility} + team"
    return visibility


@register.filter
def source_type(value):
    if value and "submission" in value:
        return "Submission"
    return str(value).capitalize()
