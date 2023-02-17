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

    return True, ''


def is_user_has_access_to_view_submission(user, submission):

    if not user.is_authenticated:
        return False, "Login Required"

    if submission.is_archive:
        if user.is_apply_staff and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF:
            return True, ''
        if user.is_apply_staff_admin and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN:
            return True, ''
        return False, "Archived Submission"

    if user.is_apply_staff or submission.user == user or user.is_reviewer:
        return True, ''

    if user.is_partner and submission.partners.filter(pk=user.pk).exists():
        return True, ''

    if user.is_community_reviewer and submission.community_review:
        return True, ''

    return False, ''


def is_user_has_access_to_view_archived_submissions(user, obj=None):
    if not user.is_authenticated:
        pass
    elif user.is_apply_staff and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF:
        return True
    elif user.is_apply_staff_admin and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN:
        return True
    return False


permissions_map = {
    'submission_view': is_user_has_access_to_view_submission,
    'submission_edit': can_edit_submission,
}
