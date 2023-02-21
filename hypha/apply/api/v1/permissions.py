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


class IsFinance1User(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_finance_level_1

    def has_object_permission(self, request, view, obj):
        return request.user.is_finance_level_1


class IsFinance2User(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_finance_level_2

    def has_object_permission(self, request, view, obj):
        return request.user.is_finance_level_2


class HasDeliverableEditPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        invoice = view.get_invoice_object()
        return invoice.can_user_edit_deliverables(request.user)
