from typing import Literal

from django import template
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.permissions import has_permission
from hypha.apply.users.models import User

register = template.Library()


def check_permission(user, perm, submission):
    if submission.is_archive:
        return False
    perm_method = getattr(submission.phase.permissions, f"can_{perm}", lambda x: False)
    return perm_method(user)


@register.filter
def has_edit_perm(user, submission):
    permission, reason = has_permission(
        "submission_edit", user=user, object=submission, raise_exception=False
    )
    return check_permission(user, "edit", submission) and permission


@register.filter
def has_review_perm(user, submission):
    return check_permission(user, "review", submission)


@register.filter
def show_applicant_identity(submission: ApplicationSubmission, user: User) -> bool:
    """Determine whether or not to display the applicant's identity.

    Args:
        submission: the submission submitted by applicant
        user: the user viewing the submission

    Returns:
        bool: True = show the applicant's identity
    """
    if (
        settings.HIDE_IDENTITY_FROM_REVIEWERS
        and not user.is_org_faculty
        and user in submission.reviewers.all()
    ):
        return False

    return True


@register.simple_tag(takes_context=True)
def get_author_display(context: dict, type: Literal["submitted", "updated"]) -> str:
    """Creates a formatted author string based on the submission and viewer role.

    Args:
        context:
            dict of template context
        type:
            A string literal of either "submitted" (retrieves author of first revision),
            or "updated" (retrieves author of live revision)

    Returns:
        A string with the formatted author depending on the user role (ie. an edit from
        staff viewed by an applicant will return the org name).
    """
    submission: ApplicationSubmission = context["object"]
    request = context["request"]

    # Should the user's name be displayed
    hide_pii = request.user != submission.user and not show_applicant_identity(
        submission, request.user
    )

    author = None
    # Edgecase handling of not having an existing revision happens for both submitted & updated
    if type == "submitted":
        first_revision = submission.revisions.order_by("timestamp").first()
        if first_revision and (first_author := first_revision.author):
            author = first_author
    elif type == "updated":
        live_revision = submission.live_revision
        if live_revision and (live_author := live_revision.author):
            author = live_author

    if author is None or hide_pii:
        return _("Applicant")

    # If staff was to edit an application (likely an edge case)
    if (
        settings.HIDE_STAFF_IDENTITY
        and author.is_org_faculty
        and not request.user.is_org_faculty
    ):
        return settings.ORG_LONG_NAME

    return str(author)
