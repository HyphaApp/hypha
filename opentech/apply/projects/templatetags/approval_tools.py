from django import template

register = template.Library()


def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()


@register.simple_tag
def user_can_approve_project(project, user):
    return user.is_approver and not user_has_approved(project, user)
