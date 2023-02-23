from django.core.exceptions import PermissionDenied

from .models.project import CLOSING, COMPLETE, CONTRACTING, IN_PROGRESS


def has_permission(action, user, object=None, raise_exception=True):
    value, reason = permissions_map[action](user, object)

    # :todo: cache the permissions based on key action:user_id:object:id
    if raise_exception and not value:
        raise PermissionDenied(reason)

    return value, reason


def can_approve_contract(user, project):
    if project.status != CONTRACTING:
        return False, 'Project is not in Contracting State'

    if not user.is_authenticated:
        return False, 'Login Required'

    if user.is_apply_staff:
        return True, 'Staff can approve the contract'

    return False, 'Forbidden Error'


def can_upload_contract(user, project):
    if project.status != CONTRACTING:
        return False, 'Project is not in Contracting State'

    if not user.is_authenticated:
        return False, 'Login Required'

    if user.is_apply_staff or user.is_contracting or user == project.user:
        return True, 'Staff and Project owner can upload the contract'

    return False, 'Forbidden Error'


def can_update_project_status(user, project):
    if project.status not in [COMPLETE, CLOSING, IN_PROGRESS]:
        return False, 'Forbidden Error'

    if not user.is_authenticated:
        return False, 'Login Required'

    if user.is_apply_staff or user.is_apply_staff_admin:
        return True, 'Staff and Staff Admin can update status'

    return False, 'Forbidden Error'


def can_update_report(user, report):
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


def can_update_report_config(user, project):
    if not user.is_authenticated:
        return False, 'Login Required'
    if project.status != IN_PROGRESS:
        return False, 'Report Config can be changed only in In Progress state'
    if user.is_apply_staff:
        return True, 'Only Staff can update report config for In Progress projects'
    return False, 'Forbidden Error'


def can_update_project_reports(user, project):
    if not user.is_authenticated:
        return False, 'Login Required'
    if project.status != IN_PROGRESS:
        return False, 'Report Config can be changed only in In Progress state'
    if user.is_apply_staff or user == project.user:
        return True, 'Only Staff and project owner can update report config for In Progress projects'
    return False, 'Forbidden Error'


def can_view_report(user, report):
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
    'project_status_update': can_update_project_status,
    'project_reports_update': can_update_project_reports,
    'report_update': can_update_report,
    'report_config_update': can_update_report_config,
    'report_view': can_view_report,
}
