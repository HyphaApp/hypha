from rest_framework import permissions


class IsAuthor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsApplyStaffUser(permissions.BasePermission):
    """
    Custom permission to only allow organisation Staff or higher
    """

    def has_permission(self, request, view):
        return request.user.is_apply_staff

    def has_object_permission(self, request, view, obj):
        return request.user.is_apply_staff


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
