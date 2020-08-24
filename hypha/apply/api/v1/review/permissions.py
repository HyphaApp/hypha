from rest_framework import permissions


class HasReviewCreatePermission(permissions.BasePermission):
    """
    Custom permission to only allow organisation Staff or higher
    """

    def has_permission(self, request, view):
        submission = view.get_submission_object()
        return (
            submission.phase.permissions.can_review(request.user) and
            submission.has_permission_to_review(request.user)
        )


class HasReviewEditPermission(permissions.BasePermission):
    """
    Custom permission to only allow organisation Staff or higher
    """

    def has_object_permission(self, request, view, obj):
        return request.user.has_perm('review.change_review') or request.user == obj.author.reviewer


class HasReviewDetialPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        author = obj.author.reviewer
        submission = obj.submission

        if user.is_apply_staff:
            return True

        if user == author:
            return True

        if user.is_reviewer and obj.reviewer_visibility:
            return True

        if user.is_community_reviewer and submission.community_review and obj.reviewer_visibility and submission.user != user:
            return True

        return False


class HasReviewDeletePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.has_perm('review.delete_review') or request.user == obj.author


class HasReviewOpinionPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        review = obj
        user = request.user
        author = review.author.reviewer
        submission = review.submission

        if user.is_apply_staff:
            return True

        if user == author:
            return False

        if user.is_reviewer and review.reviewer_visibility:
            return True

        if user.is_community_reviewer and submission.community_review and review.reviewer_visibility and submission.user != user:
            return True

        return False
