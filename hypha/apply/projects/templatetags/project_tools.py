from django import template

register = template.Library()


@register.simple_tag
def user_can_close(project, user):
    """Can the given User close the given Project"""
    if not user.is_apply_staff:
        return False

    if not project.can_close:
        return False

    return True
