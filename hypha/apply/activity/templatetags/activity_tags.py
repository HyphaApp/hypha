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
    if user.is_applicant and (
        activity.user.is_apply_staff
        or activity.user.is_finance
        or activity.user.is_contracting
    ):
        return settings.ORG_LONG_NAME
    if isinstance(activity.related_object, Review) and activity.source.user == user:
        return "Reviewer"
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

    visible_for_user = activity.visibility_for(user)

    if set(visible_for_user) & {TEAM, REVIEWER}:
        return message_data[TEAM]

    return message_data[ALL]


@register.filter
def visibility_options(activity, user) -> str:
    """Gets all visibility choices for the specified user

    Args:
        activity: An [`Activity`][hypha.apply.activity.models.Activity] object
        user: A [`User`][hypha.apply.users.models.User] object

    Returns:
        A JSON string of visibility options
    """
    has_partners = len(activity.source.partners.all()) > 0
    choices = activity.visibility_choices_for(user, has_partners)
    return json.dumps(choices)


@register.filter
def visibility_display(visibility: str, user) -> str:
    """Creates a formatted visibility string based on given visibility string and user role.

    Args:
        visibility: A visibility string (likely a constant from [activity models][hypha.apply.activity.models])
        user: The [`User`][hypha.apply.users.models.User] being shown the formatted string

    Returns:
        A formatted visibility string (ie. "ACME team" if visibility is "team" or "All" if visibility is "all").
    """
    if not user.is_apply_staff and not user.is_finance and not user.is_contracting:
        if visibility == TEAM:
            return f"{settings.ORG_SHORT_NAME} team"
        elif visibility != ALL:
            return f"{visibility.capitalize()} + {settings.ORG_SHORT_NAME} team"

    if visibility not in (TEAM, ALL):
        return f"{visibility.capitalize()} + team"

    return visibility.capitalize()


@register.filter
def source_type(value):
    if value and "submission" in value:
        return "Submission"
    return str(value).capitalize()
