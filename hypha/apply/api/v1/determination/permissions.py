from rest_framework import permissions

from hypha.apply.determinations.permissions import (
    can_create_determination,
    can_edit_determination,
)


class HasDeterminationCreatePermission(permissions.BasePermission):
    """
    Custom permission that user should have for creating determination.
    """

    def has_permission(self, request, view):
        try:
            submission = view.get_submission_object()
        except KeyError:
            return True
        return can_create_determination(request.user, submission)


class HasDeterminationDraftPermission(permissions.BasePermission):
    """
    Custom permission that user should have for editing determination.
    """

    def has_object_permission(self, request, view, obj):
        submission = view.get_submission_object()
        return can_edit_determination(request.user, obj, submission)
