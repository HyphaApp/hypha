from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from rolepermissions.permissions import register_object_checker

from hypha.apply.funds.models.co_applicants import CoApplicant, CoApplicantRole
from hypha.apply.funds.models.submissions import DRAFT_STATE

from ..users.roles import STAFF_GROUP_NAME, SUPERADMIN, TEAMADMIN_GROUP_NAME, StaffAdmin


def has_permission(action, user, object=None, raise_exception=True):
    value, reason = permissions_map[action](user, object)

    # :todo: cache the permissions based on key action:user_id:object:id
    if raise_exception and not value:
        raise PermissionDenied(reason)

    return value, reason


def can_take_submission_actions(user, submission):
    if not user.is_authenticated:
        return False, _("Login Required")

    if submission.is_archive:
        return False, _("Archived Submission")

    return True, ""


def can_edit_submission(user, submission):
    if not user.is_authenticated:
        return False, _("Login Required")

    if submission.is_archive:
        return False, _("Archived Submission")

    if submission.phase.permissions.can_edit(user):
        co_applicant = submission.co_applicants.filter(user=user).first()
        if co_applicant:
            if co_applicant.role not in [CoApplicantRole.VIEW, CoApplicantRole.COMMENT]:
                return (
                    True,
                    _(
                        "Co-applicant with read/view only or comment access can't edit submission"
                    ),
                )
            return False, ""
        return True, _("User can edit in current phase")
    return False, ""


@register_object_checker()
def view_comments(role, user, submission) -> bool:
    from hypha.apply.projects.permissions import can_access_project

    if role == StaffAdmin:
        return True

    if is_user_has_access_to_view_submission(user, submission):
        return True

    if submission.project and can_access_project(user, submission.project):
        return True

    return False


@register_object_checker()
def delete_submission(role, user, submission) -> bool:
    """
    Determines if a user has permission to delete a submission.

    Permissions are granted if:
    - User is a Superuser, or StaffAdmin
    - User has explicit delete_applicationsubmission permission
    - User is the applicant of the submission and it is in draft state
    """
    if role == StaffAdmin:
        return True

    if user.has_perm("funds.delete_applicationsubmission"):
        return True

    # Allow the user to delete their own draft submissions
    if user == submission.user and submission.status == DRAFT_STATE:
        return True

    return False


def can_bulk_delete_submissions(user) -> bool:
    if user.is_apply_staff:
        return True
    return False


def can_bulk_update_submissions(user) -> bool:
    if user.is_apply_staff:
        return True
    return False


def get_archive_view_groups() -> list:
    """
    Returns a list of groups that can view archived submissions
    """

    archive_access_view_groups = [SUPERADMIN]

    if settings.SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF:
        archive_access_view_groups.append(STAFF_GROUP_NAME)
    if settings.SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF_ADMIN:
        archive_access_view_groups.append(TEAMADMIN_GROUP_NAME)

    return archive_access_view_groups


def can_view_archived_submissions(user) -> bool:
    """
    Return a boolean based on if a user can view archived submissions
    """
    archive_view_groups = get_archive_view_groups()

    if user.is_apply_staff and STAFF_GROUP_NAME in archive_view_groups:
        return True
    if user.is_apply_staff_admin and TEAMADMIN_GROUP_NAME in archive_view_groups:
        return True
    return False


def get_archive_alter_groups() -> list:
    """
    Returns a list of groups that can archive & unarchive submissions
    """

    archive_access_groups = [SUPERADMIN]

    if settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF:
        archive_access_groups.append(STAFF_GROUP_NAME)
    if settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN:
        archive_access_groups.append(TEAMADMIN_GROUP_NAME)

    return archive_access_groups


def can_alter_archived_submissions(user, submission=None) -> (bool, str):
    """
    Return a boolean based on if a user can alter archived submissions
    """
    archive_access_groups = get_archive_alter_groups()

    if user.is_apply_staff and STAFF_GROUP_NAME in archive_access_groups:
        return True, _("Staff is set to alter archive")
    if user.is_apply_staff_admin and TEAMADMIN_GROUP_NAME in archive_access_groups:
        return True, _("Staff Admin is set to alter archive")
    return False, _("Forbidden Error")


def can_bulk_archive_submissions(user) -> bool:
    if can_alter_archived_submissions(user) and can_bulk_delete_submissions(user):
        return True

    return False


def can_change_external_reviewers(user, submission) -> bool:
    """
    External reviewers of a submission can be changed by lead and staff.

    Staff can only change external reviewers if the `GIVE_STAFF_LEAD_PERMS`
    setting is enabled. Superusers can always change external reviewers.
    """
    # check if all submissions have external review enabled
    if not submission.stage.has_external_review:
        return False

    if user.is_superuser:
        return True

    if settings.GIVE_STAFF_LEAD_PERMS and user.is_apply_staff:
        return True

    # only leads can change external reviewers
    if submission.lead.id == user.id:
        return True

    return False


def can_access_drafts(user) -> bool:
    if user.is_apply_staff and settings.SUBMISSIONS_DRAFT_ACCESS_STAFF:
        return True
    if user.is_apply_staff_admin and settings.SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN:
        return True
    return False


def can_export_submissions(user) -> bool:
    if user.is_apply_staff and settings.SUBMISSIONS_EXPORT_ACCESS_STAFF:
        return True
    if user.is_apply_staff_admin and settings.SUBMISSIONS_EXPORT_ACCESS_STAFF_ADMIN:
        return True
    return False


def is_user_has_access_to_view_submission(user, submission):
    if not user.is_authenticated:
        return False, _("Login Required")

    if submission.is_archive and not can_view_archived_submissions(user):
        return False, _("Archived Submission")

    if (
        user.is_apply_staff
        or submission.user == user
        or user.is_reviewer
        or submission.co_applicants.filter(user=user).exists()
    ):
        return True, ""

    if user.is_partner and submission.partners.filter(pk=user.pk).exists():
        return True, ""

    if user.is_community_reviewer and submission.community_review:
        return True, ""

    return False, ""


def can_view_submission_screening(user, submission):
    # __ to avoid shadowing the gettext alias
    submission_view, __ = is_user_has_access_to_view_submission(user, submission)
    if not submission_view:
        return False, _("No access to view submission")
    if submission.user == user:
        return False, _("Applicant cannot view submission screening")
    return True, ""


def can_invite_co_applicants(user, submission):
    if submission.is_archive:
        return False, _("Co-applicant can't be added to archived submission")
    if hasattr(submission, "project"):
        from hypha.apply.projects.models.project import COMPLETE

        if submission.project.status == COMPLETE:
            return False, _("Co-applicants can't be invited to completed projects")
    if (
        submission.co_applicant_invites.all().count()
        >= settings.SUBMISSIONS_COAPPLICANT_INVITES_LIMIT
    ):
        return False, _("Limit reached for this submission")
    if user.is_applicant and user == submission.user:
        return True, _("Applicants can invite co-applicants to their application")
    if user.is_apply_staff:
        return True, _("Staff can invite co-applicant on behalf of applicant")
    return False, _("Forbidden Error")


def can_view_co_applicants(user, submission):
    if user.is_applicant and user == submission.user:
        return True, _("Submission user can access their submission's co-applicants")
    if user.is_apply_staff:
        return True, _("Staff can access each submissions' co-applicants")
    return False, _("Forbidden Error")


def can_update_co_applicant(user, invite):
    if invite.submission.is_archive:
        return False, _("Co-applicant can't be updated to archived submission")
    if hasattr(invite.submission, "project"):
        from hypha.apply.projects.models.project import COMPLETE

        if invite.submission.project.status == COMPLETE:
            return False, _("Co-applicants can't be updated to completed projects")
    if invite.invited_by == user:
        return True, _("Same user who invited can delete the co-applicant")
    if invite.submission.user == user:
        return True, _("Submission owner can delete the co-applicant")
    if user.is_apply_staff:
        return True, _("Staff can delete any co-applicant of any submission")
    return False, _("Forbidden Error")


def user_can_view_post_comment_form(user, submission):
    co_applicant = CoApplicant.objects.filter(user=user, submission=submission).first()
    if co_applicant and co_applicant.role == CoApplicantRole.VIEW:
        return False
    return True


permissions_map = {
    "submission_view": is_user_has_access_to_view_submission,
    "submission_edit": can_edit_submission,
    "submission_action": can_take_submission_actions,
    "can_view_submission_screening": can_view_submission_screening,
    "archive_alter": can_alter_archived_submissions,
    "co_applicant_invite": can_invite_co_applicants,
    "co_applicants_view": can_view_co_applicants,
    "co_applicants_update": can_update_co_applicant,
}
