from django.conf import settings


def is_user_has_access_to_view_submission(user, submission):
    has_access = False

    if not user.is_authenticated:
        pass

    elif user.is_apply_staff or submission.user == user or user.is_reviewer:
        has_access = True

    elif user.is_partner and submission.partners.filter(pk=user.pk).exists():
        has_access = True

    elif user.is_community_reviewer and submission.community_review:
        has_access = True

    return has_access


def is_user_has_access_to_view_archived_submissions(user):
    if not user.is_authenticated:
        pass
    elif user.is_apply_staff and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF:
        return True
    elif user.is_apply_staff_admin and settings.SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN:
        return True
    return False
