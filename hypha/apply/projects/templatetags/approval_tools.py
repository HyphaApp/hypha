from django import template

register = template.Library()


def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()


@register.simple_tag
def can_send_for_approval(project, user):
    return user.is_apply_staff and project.can_send_for_approval


@register.simple_tag
def user_can_approve_project(project, user):
    if not user_has_approved(project, user):
        if user.is_finance or user.is_contracting or user.is_approver:
            return True
    return False


@register.simple_tag
def user_can_update_paf_status(project, user):
    if not project.user == user:
        if project.can_update_paf_status:
            if user.is_finance or user.is_contracting or user.is_approver:
                return True
    return False


@register.simple_tag
def user_can_final_approve_project(project, user):
    if user.is_approver and user.is_contracting and project.can_make_final_approval:
        return True
    return False


@register.simple_tag
def user_can_edit_project(project, user):
    return project.editable_by(user)
