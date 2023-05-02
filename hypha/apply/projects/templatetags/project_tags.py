from django import template
from django.urls import reverse

from hypha.apply.projects.models.project import (
    CLOSING,
    COMPLETE,
    CONTRACTING,
    DRAFT,
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
    if project.status == DRAFT:
        if user.is_apply_staff:
            if not project.user_has_updated_details:
                return "Fill in the Approval Form(PAF)"
            if project.paf_approvals.exists():
                return "Resubmit project documents for approval"
            return "Submit project documents for approval"
        if project.paf_approvals.exists():
            return "Changes requested. Awaiting documents to be resubmitted."
        return "Awaiting approval form to be created."
    elif project.status == WAITING_FOR_APPROVAL:
        if user.id in project.paf_approvals.values_list('user', flat=True):
            return "Awaiting project approval from assigned approvers. Please review and update status"
        if user.is_applicant:
            return "Awaiting approval form to be approved."
        return "Awaiting project approval from assigned approvers"
    elif project.status == CONTRACTING:
        if not project.contracts.exists():
            return "Awaiting signed contract from Contracting team"
        else:
            contract = project.contracts.order_by('-created_at').first()
            if not contract.signed_by_applicant:
                if user.is_applicant:
                    return "Awaiting contract documents to be submitted by applicant."
                return "Awaiting countersigned contract from Applicant"
            elif not project.submitted_contract_documents:
                return "Awaiting contract documents submission from Applicant"
            else:
                if user.is_apply_staff:
                    return "Review the contract for all relevant details and approve."
                return "Awaiting contract approval from Staff"
    elif project.status == IN_PROGRESS:
        if user.is_applicant:
            return "Add invoices"
        elif user.is_apply_staff or user.is_finance:
            return "Review invoice and take action"
    return False


@register.simple_tag
def user_next_step_instructions(project, user):
    """
    To provide instructions incase next step is not enough like 'contracting documents submitted by an applicant'
    """
    if project.status == CONTRACTING and user == project.user and project.contracts.exists():
        contract = project.contracts.order_by('-created_at').first()
        if contract and not contract.signed_by_applicant:
            return ['Please download the signed contract uploaded by contracting team',
                    'Countersign',
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
    if project.status in [DRAFT, WAITING_FOR_APPROVAL]:
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


@register.simple_tag
def allow_collapsible_header(project, header_type):
    if header_type == 'project_documents' and project.status not in [DRAFT, WAITING_FOR_APPROVAL]:
        return True
    if header_type == 'contracting_documents' and project.status not in [DRAFT, WAITING_FOR_APPROVAL, CONTRACTING]:
        return True
    return False


@register.simple_tag
def user_can_remove_supporting_documents(project, user):
    if user.is_apply_staff and project.status == DRAFT:
        return True
    return False


@register.simple_tag
def user_can_take_actions(project, user):
    """
    Checking permissions for 'Action to take' section on paf approval details page.
    """
    if user.is_apply_staff or user.is_contracting:
        return True
    if user.id in project.paf_approvals.values_list('user', flat=True):
        return True
    return False
