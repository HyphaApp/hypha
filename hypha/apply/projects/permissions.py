from django.core.exceptions import PermissionDenied

from .models.project import (
    CLOSING,
    COMPLETE,
    CONTRACTING,
    IN_PROGRESS,
    WAITING_FOR_APPROVAL,
    ProjectSettings,
)


def has_permission(action, user, object=None, raise_exception=True, **kwargs):
    value, reason = permissions_map[action](user, object, **kwargs)

    # :todo: cache the permissions based on key action:user_id:object:id
    if raise_exception and not value:
        raise PermissionDenied(reason)

    return value, reason


def can_approve_contract(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, 'Project is not in Contracting State'

    if not project.submitted_contract_documents:
        return False, 'No contract documents submission yet'

    if not user.is_authenticated:
        return False, 'Login Required'

    if user.is_apply_staff and not user.is_contracting and not user.is_applicant:
        return True, 'Only Staff can approve the contract'

    return False, 'Forbidden Error'


def can_upload_contract(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, 'Project is not in Contracting State'

    if not user.is_authenticated:
        return False, 'Login Required'

    if user == project.user and project.contracts.exists():
        return True, 'Project Owner can only re-upload contract with counter-sign'

    if user.is_contracting:
        return True, 'Contracting team can upload the contract'

    return False, 'Forbidden Error'


def can_submit_contract_documents(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, 'Project is not in Contracting State'
    if user != project.user:
        return False, 'Only Applicant can submit contracting documents'
    if not kwargs.get('contract', None):
        return False, 'Can not submit without contract'
    if not project.submitted_contract_documents:
        return True, 'Applicant can submit contracting documents'

    return False, 'Forbidden Error'


def can_update_paf_status(user, project, **kwargs):
    if not user.is_authenticated:
        return False, 'Login Required'

    if not project.paf_approvals.filter(approved=False).exists():
        return False, 'No PAF Approvals Exists'

    if project.status != WAITING_FOR_APPROVAL:
        return False, 'Incorrect project status to approve PAF'

    request = kwargs.get('request')
    if request:
        project_settings = ProjectSettings.for_request(request)
        if project_settings.paf_approval_sequential:
            if user.id == project.paf_approvals.filter(approved=False).first().user.id:
                return True, 'Next Approver can approve PAF(For Sequential Approvals)'
            return False, 'Only Next can approve PAF(For Sequential Approvals)'
        if user.id in project.paf_approvals.filter(approved=False).values_list('user', flat=True):
            return True, 'All assigned approvers can approve PAF(For Parallel Approvals)'

        return False, 'Unable to access the Project Settings'

    return False, 'Forbidden Error'


def can_update_project_status(user, project, **kwargs):
    if project.status not in [COMPLETE, CLOSING, IN_PROGRESS]:
        return False, 'Forbidden Error'

    if not user.is_authenticated:
        return False, 'Login Required'

    if user.is_apply_staff or user.is_apply_staff_admin:
        return True, 'Staff and Staff Admin can update status'

    return False, 'Forbidden Error'


def can_update_report(user, report, **kwargs):
    if not user.is_authenticated:
        return False, 'Login Required'
    if report.project.status != IN_PROGRESS:
        return False, 'Report can be updated only in In Progress state'
    if report.skipped:
        return False, 'Skipped reports are not editable'
    if not report.can_submit:
        return False, 'Future reports are not editable'

    if user.is_apply_staff or (user == report.project.user and not report.current):
        return True, 'Staff and Project Owner can edit the editable reports'

    return False, 'Forbidden Error'


def can_update_report_config(user, project, **kwargs):
    if not user.is_authenticated:
        return False, 'Login Required'
    if project.status != IN_PROGRESS:
        return False, 'Report Config can be changed only in In Progress state'
    if user.is_apply_staff:
        return True, 'Only Staff can update report config for In Progress projects'
    return False, 'Forbidden Error'


def can_update_project_reports(user, project, **kwargs):
    if not user.is_authenticated:
        return False, 'Login Required'
    if project.status != IN_PROGRESS:
        return False, 'Report Config can be changed only in In Progress state'
    if user.is_apply_staff or user == project.user:
        return True, 'Only Staff and project owner can update report config for In Progress projects'
    return False, 'Forbidden Error'


def can_view_report(user, report, **kwargs):
    if not user.is_authenticated:
        return False, 'Login Required'
    if report.project.status not in [COMPLETE, CLOSING, IN_PROGRESS]:
        return False, 'Report are not available at this state'
    if not report.current:
        return False, 'Only current reports can be viewed'
    if report.skipped:
        return False, 'Skipped reports are not available'
    if user.is_apply_staff or user.is_finance or user == report.project.user:
        return True, 'Staff, Finance, and Project owner can view the report'
    return False, 'Forbidden Error'


permissions_map = {
    'contract_approve': can_approve_contract,
    'contract_upload': can_upload_contract,
    'paf_status_update': can_update_paf_status,
    'project_status_update': can_update_project_status,
    'project_reports_update': can_update_project_reports,
    'report_update': can_update_report,
    'report_config_update': can_update_report_config,
    'report_view': can_view_report,
    'submit_contract_documents': can_submit_contract_documents,
}
