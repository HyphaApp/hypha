from django import template
from django.urls import reverse

from hypha.apply.projects.models.project import (
    CLOSING,
    COMMITTED,
    COMPLETE,
    CONTRACTING,
    IN_PROGRESS,
    WAITING_FOR_APPROVAL,
)
from hypha.apply.projects.permissions import has_permission

register = template.Library()


@register.simple_tag
def project_can_have_report(project):
    if project.status in [COMPLETE, CLOSING, IN_PROGRESS]:
        return True
    return False


@register.simple_tag
def user_next_step_on_project(project, user):
    if project.status == COMMITTED:
        if not project.user_has_updated_details:
            return "Awaiting PAF to be filled in from Lead/Staff"
        return "Awaiting PAF submission for Approval from Lead/Staff"
    elif project.status == WAITING_FOR_APPROVAL:
        return "Awaiting PAF Approvals from assigned approvers"
    elif project.status == CONTRACTING:
        if not project.contracts.exists():
            return "Awaiting signed contract from Contracting team"
        else:
            contract = project.contracts.order_by('-created_at').first()
            if not contract.signed_by_applicant:
                if user.is_applicant:
                    return "Awaiting counter-signed contract and contracting documents from Applicant."
                return "Awaiting counter-signed contract from Applicant"
            elif not project.submitted_contract_documents:
                return "Awaiting contract documents submission from Applicant"
            else:
                return "Awaiting contract approval from Staff"
    return False


@register.simple_tag
def user_next_step_instructions(project, user):
    if project.status == CONTRACTING and user == project.user and project.contracts.exists():
        contract = project.contracts.order_by('-created_at').first()
        if contract and not contract.signed_by_applicant:
            return ['Please download the signed contract uploaded by contracting team',
                    'Counter Sign',
                    'Upload it back',
                    'Please also make sure to upload other required contracting documents']
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
def project_can_have_contracting_section(project):
    if project.status in [COMMITTED, WAITING_FOR_APPROVAL]:
        return False
    return True


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
