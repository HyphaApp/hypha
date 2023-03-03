from django import template

from ..permissions import has_permission

register = template.Library()


def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()


@register.simple_tag
def user_can_send_for_approval(project, user):
    return user.is_apply_staff and project.can_send_for_approval


@register.simple_tag
def user_can_approve_project(project, user):
    if not user_has_approved(project, user):
        if user.is_finance or user.is_contracting or user.is_approver:
            return True
    return False


@register.simple_tag
def user_can_update_paf_status(project, user, **kwargs):
    request = kwargs.get('request')
    if request:
        permission, _ = has_permission('paf_status_update', user, object=project, raise_exception=False, request=request)
        return permission
    return False


@register.simple_tag
def user_can_final_approve_project(project, user):
    if user.is_approver and user.is_contracting and project.ready_for_final_approval:
        return True
    return False


@register.simple_tag
def user_can_edit_project(project, user):
    return project.editable_by(user)
