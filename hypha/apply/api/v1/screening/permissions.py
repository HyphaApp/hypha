from rest_framework import permissions


class HasScreenPermission(permissions.BasePermission):
    """
    Custom permission that user should have for screening the submission
    """

    def has_permission(self, request, view):
        try:
            submission = view.get_submission_object()
        except KeyError:
            return True
        if submission.is_archive:
            return False
        return True
