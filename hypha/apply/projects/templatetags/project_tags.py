from django import template
from django.conf import settings
from django.db.models import Count
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
def user_next_step_on_project(project, user, request=None):
    from hypha.apply.projects.models.project import PAFReviewersRole, ProjectSettings
    if project.status == DRAFT:
        if user.is_apply_staff:
            if not project.user_has_updated_details:
                return "Fill in the Approval Form(PAF)"
            if project.paf_approvals.exists():
                return "Resubmit project documents for approval"
            return "Submit project documents for approval"
        elif user.is_applicant:
            return "Awaiting project documents to be created and approved by OTF internally. " \
                   "Please check back when the project has moved to contracting stage."
        if project.paf_approvals.exists():
            return "Changes requested. Awaiting documents to be resubmitted."
        return "Awaiting approval form to be created."
    elif project.status == WAITING_FOR_APPROVAL:
        if user.is_applicant:
            return "Awaiting project documents to be created and approved by OTF internally. " \
                   "Please check back when the project has moved to contracting stage."

        if request:
            project_settings = ProjectSettings.for_request(request=request)
            if project_settings.paf_approval_sequential:
                latest_unapproved_approval = project.paf_approvals.filter(approved=False).first()
                if latest_unapproved_approval:
                    if latest_unapproved_approval.user:
                        return f"Awaiting approval. Assigned to {latest_unapproved_approval.user}"
                    return f"Awaiting {latest_unapproved_approval.paf_reviewer_role.label} to assign an approver"
            else:
                matched_roles = PAFReviewersRole.objects.annotate(roles_count=Count('user_roles')).filter(
                    roles_count=len(user.groups.all()))
                for group in user.groups.all():
                    matched_roles = matched_roles.filter(user_roles__id=group.id)
                if not matched_roles:
                    return "Awaiting PAF approval form to be approved"
                else:
                    matched_unapproved_approval = project.paf_approvals.filter(approved=False, paf_reviewer_role__in=matched_roles)
                    if not matched_unapproved_approval.exists():
                        return "Awaiting approval from other approvers teams"
                    else:
                        if matched_unapproved_approval.first().user:
                            return f"Awaiting approval. Assigned to {matched_unapproved_approval.first().user}"
                        return f"Awaiting {matched_unapproved_approval.first().paf_reviewer_role.label} to assign an approver"

        return "Awaiting project approval from assigned approvers"
    elif project.status == CONTRACTING:
        if not project.contracts.exists():
            if user.is_applicant:
                return f"Awaiting signed contract from {settings.ORG_SHORT_NAME}"
            return "Awaiting signed contract from Contracting team"
        else:
            contract = project.contracts.order_by('-created_at').first()
            if not contract.signed_by_applicant:
                if user.is_applicant:
                    return "Awaiting contract documents to be submitted by you."
                return "Awaiting countersigned contract from Vendor"
            elif not project.submitted_contract_documents:
                if user.is_applicant:
                    return "Awaiting contract documents submission by you"
                return "Awaiting contract documents submission from Vendor"
            else:
                if user.is_apply_staff:
                    return "Review the contract for all relevant details and approve."
                if user.is_applicant:
                    return f"Awaiting contract approval from {settings.ORG_SHORT_NAME}"
                return f"Awaiting contract approval from Staff"
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


@register.simple_tag
def category_latest_file(project, category):
    return category.packet_files.filter(project=project).first()


@register.simple_tag
def contract_category_latest_file(project, category):
    return category.contract_packet_files.filter(project=project).first()
