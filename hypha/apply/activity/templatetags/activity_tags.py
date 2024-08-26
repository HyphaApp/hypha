import json

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.translation import gettext_lazy as _

from hypha.apply.determinations.models import Determination
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.projects.models import Contract
from hypha.apply.review.models import Review
from hypha.apply.users.models import User

from ..models import ALL, APPLICANT_PARTNERS, REVIEWER, TEAM

register = template.Library()


@register.filter
def display_activity_author(activity, user) -> str:
    """Creates a formatted author string based on the activity and viewer role.

    Args:
        activity:
            An [`Activity`][hypha.apply.activity.models.Activity] object
        user:
            The [`User`][hypha.apply.users.models.User] that is viewing the
            given activity

    Returns:
        A string with the formatted author depending on the user role (ie. a
        comment from staff viewed by an applicant will return the org name).
    """
    if (
        settings.HIDE_STAFF_IDENTITY
        and not user.is_org_faculty
        and activity.user.is_org_faculty
    ):
        return settings.ORG_LONG_NAME

    if isinstance(activity.related_object, Review) and activity.source.user == user:
        return _("Reviewer")

    if (
        settings.HIDE_IDENTITY_FROM_REVIEWERS
        and isinstance(activity.source, ApplicationSubmission)
        and activity.user == activity.source.user
        and user in activity.source.reviewers.all()
    ):
        return _("Applicant")

    return activity.user.get_display_name()


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
        activity:
            An [`Activity`][hypha.apply.activity.models.Activity] object
        user:
            A [`User`][hypha.apply.users.models.User] object

    Returns:
        A JSON string of visibility options
    """
    submission_partner_list = activity.source.partners.all()
    choices = activity.visibility_choices_for(user, submission_partner_list)
    return json.dumps(choices)


@register.filter
def visibility_display(visibility: str, user) -> str:
    """Creates a formatted visibility string with visibility string and user.

    Args:
        visibility:
            A visibility string (likely a constant from [activity models][hypha.apply.activity.models])
        user:
            [`User`][hypha.apply.users.models.User] to be shown the formatted string

    Returns:
        A formatted visibility string (ie. "ACME team" if visibility is "team"
        and user is applicant or "all" if visibility is "all").
    """
    if not user.is_apply_staff and not user.is_finance and not user.is_contracting:
        team_string = f"{settings.ORG_SHORT_NAME} {TEAM}"
    else:
        team_string = TEAM

    if visibility == APPLICANT_PARTNERS:
        visibility = " + ".join(visibility.split())

    if visibility == TEAM:
        return team_string

    if visibility not in (TEAM, ALL):
        return f"{visibility} + {team_string}"

    return visibility


@register.simple_tag(takes_context=True)
def display_name_for_email(context: dict, user: User) -> str:
    """Gets a user's display name when being used in an email
    Primarily used to hide staff identities
    Args:
        user: the [`User`][hypha.apply.users.models.User] to get the display name for
        context: the context provided by the template
    Returns:
        str: the display name to be used to address the user in question
    """
    recipient = context["recipient"]

    if (
        settings.HIDE_STAFF_IDENTITY
        and user.is_org_faculty
        and not recipient.is_org_faculty
    ):
        return settings.ORG_LONG_NAME
    else:
        return str(user)


@register.filter
def source_type(value) -> str:
    """Formats source type
    For a given source type containing "submission", this will be converted
    to "Submission" (ie. "application submission" -> "Submission").
    Args:
        value: the source type to be formatted
    Returns:
        A source type string with a capitalized first letter
    """
    if value and "submission" in value:
        return "Submission"
    return str(value).capitalize()


@register.filter(is_safe=True)
@stringfilter
def lowerfirst(value):
    """Lowercase the first character of the value."""
    return value and value[0].lower() + value[1:]
