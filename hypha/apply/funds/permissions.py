from django.conf import settings
from django.core.exceptions import PermissionDenied
from rolepermissions.permissions import register_object_checker

from hypha.apply.funds.models.submissions import DRAFT_STATE

from ..users.roles import STAFF_GROUP_NAME, SUPERADMIN, TEAMADMIN_GROUP_NAME, StaffAdmin


def has_permission(action, user, object=None, raise_exception=True):
    value, reason = permissions_map[action](user, object)

    # :todo: cache the permissions based on key action:user_id:object:id
    if raise_exception and not value:
        raise PermissionDenied(reason)

    return value, reason


def can_edit_submission(user, submission):
    if not user.is_authenticated:
        return False, "Login Required"

    if submission.is_archive:
        return False, "Archived Submission"

    return True, ""


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
        return True, "Staff is set to alter archive"
    if user.is_apply_staff_admin and TEAMADMIN_GROUP_NAME in archive_access_groups:
        return True, "Staff Admin is set to alter archive"
    return False, "Forbidden Error"


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
        return False, "Login Required"

    if submission.is_archive and not can_view_archived_submissions(user):
        return False, "Archived Submission"

    if user.is_apply_staff or submission.user == user or user.is_reviewer:
        return True, ""

    if user.is_partner and submission.partners.filter(pk=user.pk).exists():
        return True, ""

    if user.is_community_reviewer and submission.community_review:
        return True, ""

    return False, ""


def can_view_submission_screening(user, submission):
    submission_view, _ = is_user_has_access_to_view_submission(user, submission)
    if not submission_view:
        return False, "No access to view submission"
    if submission.user == user:
        return False, "Applicant cannot view submission screening"
    return True, ""


permissions_map = {
    "submission_view": is_user_has_access_to_view_submission,
    "submission_edit": can_edit_submission,
    "can_view_submission_screening": can_view_submission_screening,
    "archive_alter": can_alter_archived_submissions,
}
