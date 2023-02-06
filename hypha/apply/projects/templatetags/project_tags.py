from django import template

from hypha.apply.projects.models.project import CLOSING, COMPLETE, IN_PROGRESS

register = template.Library()


@register.simple_tag
def user_can_view_reports(project, user):
    if project.status in [COMPLETE, CLOSING, IN_PROGRESS]:
        return True
    return False


@register.simple_tag
def user_can_add_reports(project, user):
    if project.status == IN_PROGRESS:
        return True
    return False


@register.simple_tag
def user_can_edit_reports(project, user):
    if project.status == IN_PROGRESS:
        return True
    return False


@register.simple_tag
def can_access_supporting_documents_section(project):
    if project.status not in [IN_PROGRESS, CLOSING, COMPLETE]:
        return True
    return False


@register.simple_tag
def show_closing_banner(project):
    if project.status in [COMPLETE, CLOSING]:
        return True
    return False
