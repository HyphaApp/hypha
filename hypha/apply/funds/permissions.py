from django.conf import settings
from django.core.exceptions import PermissionDenied


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


def can_bulk_delete_submissions(user) -> bool:
    if user.is_apply_staff:
        return True
    return False


def can_access_archived_submissions(user):
    if user.is_apply_staff and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF:
        return True
    if user.is_apply_staff_admin and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN:
        return True
    return False


def can_bulk_archive_submissions(user) -> bool:
    if can_access_archived_submissions(user) and can_bulk_delete_submissions(user):
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


def can_access_drafts(user):
    if user.is_apply_staff and settings.SUBMISSIONS_DRAFT_ACCESS_STAFF:
        return True
    if user.is_apply_staff_admin and settings.SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN:
        return True
    return False


def is_user_has_access_to_view_submission(user, submission):
    if not user.is_authenticated:
        return False, "Login Required"

    if submission.is_archive and not can_access_archived_submissions(user):
        return False, "Archived Submission"

    if user.is_apply_staff or submission.user == user or user.is_reviewer:
        return True, ""

    if user.is_partner and submission.partners.filter(pk=user.pk).exists():
        return True, ""

    if user.is_community_reviewer and submission.community_review:
        return True, ""

    return False, ""


permissions_map = {
    "submission_view": is_user_has_access_to_view_submission,
    "submission_edit": can_edit_submission,
}
