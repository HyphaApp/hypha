from django import template
from django.urls import reverse

from hypha.apply.projects.models.project import CLOSING, COMPLETE, IN_PROGRESS
from hypha.apply.projects.permissions import has_permission

register = template.Library()


@register.simple_tag
def project_can_have_report(project):
    if project.status in [COMPLETE, CLOSING, IN_PROGRESS]:
        return True
    return False


@register.simple_tag
def user_can_update_project_reports(project, user):
    permission, _ = has_permission('project_reports_update', user, object=project, raise_exception=False)
    return permission


@register.simple_tag
def user_can_update_report_config(project, user):
    permission, _ = has_permission('report_config_update', user, object=project, raise_exception=False)
    return permission


@register.simple_tag
def user_can_update_report(report, user):
    permission, _ = has_permission('report_update', user, object=report, raise_exception=False)
    return permission


@register.simple_tag
def user_can_view_report(report, user):
    permission, _ = has_permission('report_view', user, object=report, raise_exception=False)
    return permission


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


@register.simple_tag
def user_can_update_project_status(project, user):
    can_update_status, _ = has_permission('project_status_update', user, object=project, raise_exception=False)
    return can_update_status


@register.simple_tag
def project_settings_url(instance):
    return reverse(
        "wagtailsettings:edit",
        args=[
            instance._meta.app_label,
            instance._meta.model_name,
            instance.site_id,
        ],
    )
