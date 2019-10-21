from django import template

register = template.Library()


def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()


@register.simple_tag
def can_send_for_approval(project, user):
    return user.is_staff and project.can_send_for_approval


@register.simple_tag
def user_can_approve_project(project, user):
    return user.is_approver and not user_has_approved(project, user)


@register.simple_tag
def user_can_edit_project(project, user):
    return project.editable_by(user)
