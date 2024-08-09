from django import template
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.users.models import User

register = template.Library()


def check_permission(user, perm, submission):
    if submission.is_archive:
        return False
    perm_method = getattr(submission.phase.permissions, f"can_{perm}", lambda x: False)
    return perm_method(user)


@register.filter
def has_edit_perm(user, submission):
    return check_permission(user, "edit", submission)


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
def display_submission_author(context: dict, revision_author: bool = False) -> str:
    """Creates a formatted author string based on the submission and viewer role.

    Args:
        context: dict of template context
        revision_author: if True, gets revision author. False (default) gets submission author

    Returns:
        A string with the formatted author depending on the user role (ie. a
        comment from staff viewed by an applicant will return the org name).
    """
    submission: ApplicationSubmission = context["object"]
    request = context["request"]

    author = submission.user if not revision_author else submission.live_revision.author
    if (
        not revision_author or author == submission.user
    ) and not show_applicant_identity(submission, request.user):
        return _("Applicant")
    elif (
        settings.HIDE_STAFF_IDENTITY
        and author.is_org_faculty
        and not request.user.is_org_faculty
    ):
        return settings.ORG_LONG_NAME  # Likely an edge case but covering bases

    return str(author)
