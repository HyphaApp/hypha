from django import template

register = template.Library()


@register.simple_tag
def user_has_approved(project, user):
    """Has the given User already approved the given Project"""
    return project.approvals.filter(by=user).exists()
