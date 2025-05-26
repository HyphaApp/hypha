from rolepermissions.permissions import register_object_checker

from hypha.apply.funds.models.co_applicants import EDIT, CoApplicantProjectPermission
from hypha.apply.users.roles import Applicant, StaffAdmin

from ..models.project import (
    CLOSING,
    COMPLETE,
    INVOICING_AND_REPORTING,
)


@register_object_checker()
def update_project_reports(role, user, project) -> bool:
    """
    Determines if a user can update project reports.

    Args:
        role: The role of the user.
        user: The user attempting to update project reports.
        project: The project whose reports are being updated.

    Returns:
        bool: True if the user can update project reports, False otherwise.

    Conditions:
        - User must be authenticated
        - Project status must be INVOICING_AND_REPORTING
        - User must be a StaffAdmin or the project owner
    """
    if not user.is_authenticated:
        return False
    if project.status != INVOICING_AND_REPORTING:
        return False
    if role == StaffAdmin:
        return True
    if role == Applicant:
        if user == project.user:
            return True
        co_applicant = project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.REPORTS in co_applicant.project_permission
            and co_applicant.role == EDIT
        ):
            return True
    return False


@register_object_checker()
def update_report_config(role, user, project) -> bool:
    """
    Determines if a user can update the report configuration for a project.

    Args:
        role: The role of the user.
        user: The user attempting to update the report configuration.
        project: The project whose report configuration is being updated.

    Returns:
        bool: True if the user can update the report configuration, False otherwise.

    Conditions:
        - User must be authenticated
        - Project status must be INVOICING_AND_REPORTING
        - Disallow if only one time reporting is allowed and is up to date
        - User must have apply staff permissions
    """
    if not user.is_authenticated:
        return False
    if project.status != INVOICING_AND_REPORTING:
        return False

    if project.report_config.does_not_repeat and project.report_config.is_up_to_date():
        return False

    if user.is_apply_staff:
        return True
    return False


@register_object_checker()
def view_report(role, user, report) -> bool:
    """
    Determines if a user can view a report.

    Args:
        role: The role of the user.
        user: The user attempting to view the report.
        report: The report being accessed.

    Returns:
        bool: True if the user can view the report, False otherwise.

    Conditions:
        - User must be authenticated
        - Project status must be in COMPLETE, CLOSING, or INVOICING_AND_REPORTING
        - Report must be current and not skipped
        - User must be apply staff or the project owner
    """
    if not user.is_authenticated:
        return False
    if report.project.status not in [COMPLETE, CLOSING, INVOICING_AND_REPORTING]:
        return False
    if not report.current:
        return False
    if report.skipped:
        return False
    if user.is_apply_staff or user.is_finance:
        return True
    if role == Applicant:
        if user == report.project.user:
            return True
        co_applicant = report.project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.REPORTS in co_applicant.project_permission
        ):
            return True
    return False


@register_object_checker()
def update_report(role, user, report) -> bool:
    """
    Determines if a user can update a report.

    Args:
        role: The role of the user.
        user: The user attempting to update the report.
        report: The report being updated.

    Returns:
        bool: True if the user can update the report, False otherwise.

    Conditions:
        - User must be authenticated
        - Project status must be INVOICING_AND_REPORTING
        - Report must not be skipped
        - Report must be in a state that can be submitted
        - User must be apply staff or the project owner (and report not current)
    """
    if not user.is_authenticated:
        return False
    if report.project.status != INVOICING_AND_REPORTING:
        return False
    if report.skipped:
        return False
    if not report.can_submit:
        return False

    if user.is_apply_staff:
        return True

    if role == Applicant:
        if user == report.project.user and not report.current:
            return True
        co_applicant = report.project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and not report.current
            and CoApplicantProjectPermission.REPORTS in co_applicant.project_permission
            and co_applicant.role == EDIT
        ):
            return True

    return False
