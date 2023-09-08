from django.core.exceptions import PermissionDenied

from hypha.apply.activity.adapters.utils import get_users_for_groups

from .models.project import (
    CLOSING,
    COMPLETE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
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
        return False, "Project is not in Contracting State"

    if not project.submitted_contract_documents:
        return False, "No contract documents submission yet"

    if not user.is_authenticated:
        return False, "Login Required"

    if user.is_apply_staff and not user.is_contracting and not user.is_applicant:
        return True, "Only Staff can approve the contract"

    return False, "Forbidden Error"


def can_upload_contract(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, "Project is not in Contracting State"

    if not user.is_authenticated:
        return False, "Login Required"

    if user == project.user and project.contracts.exists():
        return True, "Project Owner can only re-upload contract with countersigned"

    if user.is_contracting:
        return True, "Contracting team can upload the contract"

    return False, "Forbidden Error"


def can_submit_contract_documents(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, "Project is not in Contracting State"
    if user != project.user:
        return False, "Only Vendor can submit contracting documents"
    if not kwargs.get("contract", None):
        return False, "Can not submit without contract"
    if not project.submitted_contract_documents:
        return True, "Vendor can submit contracting documents"

    return False, "Forbidden Error"


def can_update_paf_approvers(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"

    if project.status != INTERNAL_APPROVAL:
        return False, "PAF Approvers can be updated only in Internal approval state"
    if user == project.lead:
        return True, "Lead can update approvers in approval state"
    if not project.paf_approvals.exists():
        return (
            False,
            "No user can update approvers without paf approval, except lead(lead can add paf approvals)",
        )

    request = kwargs.get("request")
    project_settings = ProjectSettings.for_request(request)
    if project_settings.paf_approval_sequential:
        next_paf_approval = project.paf_approvals.filter(approved=False).first()
        if next_paf_approval:
            if next_paf_approval.user and user in get_users_for_groups(
                list(next_paf_approval.paf_reviewer_role.user_roles.all()),
                exact_match=True,
            ):
                return (
                    True,
                    "PAF Reviewer-roles users can update next approval approvers if any approvers assigned",
                )
        return False, "Forbidden Error"
    else:
        approvers_ids = []
        for approval in project.paf_approvals.filter(
            approved=False, user__isnull=False
        ):
            approvers_ids.extend(
                assigner.id
                for assigner in get_users_for_groups(
                    list(approval.paf_reviewer_role.user_roles.all()), exact_match=True
                )
            )
        if user.id in approvers_ids:
            return True, "PAF Reviewer-roles users can update approvers"
    return False, "Forbidden Error"


def can_update_assigned_paf_approvers(user, project, **kwargs):
    """
    Only for Approvers teams members(with PAFReviewerRoles' user_roles' users)
    UpdateAssignApproversView will be used by only approvers teams members.
    """
    if not user.is_authenticated:
        return False, "Login Required"
    if project.status != INTERNAL_APPROVAL:
        return False, "PAF approvers can be assigned only in Internal approval state"
    if not project.paf_approvals.exists():
        return False, "No user can assign approvers with paf_approvals"

    request = kwargs.get("request")
    project_settings = ProjectSettings.for_request(request)
    if project_settings.paf_approval_sequential:
        next_paf_approval = project.paf_approvals.filter(approved=False).first()
        if next_paf_approval:
            if user in get_users_for_groups(
                list(next_paf_approval.paf_reviewer_role.user_roles.all()),
                exact_match=True,
            ):
                return True, "PAF Reviewer-roles users can assign approvers"
            return False, "Forbidden Error"
        return False, "Forbidden Error"
    else:
        assigners_ids = []
        for approval in project.paf_approvals.filter(approved=False):
            assigners_ids.extend(
                assigner.id
                for assigner in get_users_for_groups(
                    list(approval.paf_reviewer_role.user_roles.all()), exact_match=True
                )
            )
        if user.id in assigners_ids:
            return True, "PAF Reviewer-roles users can assign approvers"
    return False, "Forbidden Error"


def can_assign_paf_approvers(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"

    if project.status != INTERNAL_APPROVAL:
        return False, "PAF approvers can be assigned only in Internal approval state"
    if not project.paf_approvals.exists():
        return False, "No user can assign approvers with paf_approvals"

    request = kwargs.get("request")
    project_settings = ProjectSettings.for_request(request)
    if project_settings.paf_approval_sequential:
        next_paf_approval = project.paf_approvals.filter(approved=False).first()
        if next_paf_approval:
            if next_paf_approval.user:
                return False, "User already assigned"
            else:
                if user in get_users_for_groups(
                    list(next_paf_approval.paf_reviewer_role.user_roles.all()),
                    exact_match=True,
                ):
                    return True, "PAF Reviewer-roles users can assign approvers"
            return False, "Forbidden Error"
        return False, "Forbidden Error"
    else:
        assigners_ids = []
        for approval in project.paf_approvals.filter(approved=False, user__isnull=True):
            assigners_ids.extend(
                assigner.id
                for assigner in get_users_for_groups(
                    list(approval.paf_reviewer_role.user_roles.all()), exact_match=True
                )
            )

        if user.id in assigners_ids:
            return True, "PAF Reviewer-roles users can assign approvers"
    return False, "Forbidden Error"


def can_update_paf_status(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"

    if not project.paf_approvals.filter(approved=False).exists():
        return False, "No PAF Approvals Exists"

    if project.status != INTERNAL_APPROVAL:
        return False, "Incorrect project status to approve PAF"

    request = kwargs.get("request")
    if request:
        project_settings = ProjectSettings.for_request(request)
        if project_settings.paf_approval_sequential:
            approval = project.paf_approvals.filter(approved=False).first()
            possible_approvers_ids = [
                role_user.id
                for role_user in get_users_for_groups(
                    list(approval.paf_reviewer_role.user_roles.all()), exact_match=True
                )
            ]
            if user.id in possible_approvers_ids:
                return (
                    True,
                    "Next approval group users can approve PAF(For Sequential Approvals)",
                )
            return (
                False,
                "Only Next approval group can approve PAF(For Sequential Approvals)",
            )
        else:
            possible_approvers_ids = []
            for approval in project.paf_approvals.filter(approved=False):
                possible_approvers_ids.extend(
                    [
                        role_user.id
                        for role_user in get_users_for_groups(
                            list(approval.paf_reviewer_role.user_roles.all()),
                            exact_match=True,
                        )
                    ]
                )
            if user.id in possible_approvers_ids:
                return (
                    True,
                    "All approval group users can approve PAF(For Parallel Approvals)",
                )
            return (
                False,
                "Only approval group users can approve PAF(For Parallel Approvals)",
            )

    return False, "Forbidden Error"


def can_update_project_status(user, project, **kwargs):
    if project.status not in [COMPLETE, CLOSING, INVOICING_AND_REPORTING]:
        return False, "Forbidden Error"

    if not user.is_authenticated:
        return False, "Login Required"

    if user.is_apply_staff or user.is_apply_staff_admin:
        return True, "Staff and Staff Admin can update status"

    return False, "Forbidden Error"


def can_update_report(user, report, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"
    if report.project.status != INVOICING_AND_REPORTING:
        return False, "Report can be updated only in Invoicing and reporting state"
    if report.skipped:
        return False, "Skipped reports are not editable"
    if not report.can_submit:
        return False, "Future reports are not editable"

    if user.is_apply_staff or (user == report.project.user and not report.current):
        return True, "Staff and Project Owner can edit the editable reports"

    return False, "Forbidden Error"


def can_update_report_config(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"
    if project.status != INVOICING_AND_REPORTING:
        return (
            False,
            "Report Config can be changed only in Invoicing and reporting state",
        )
    if user.is_apply_staff:
        return (
            True,
            "Only Staff can update report config for Invoicing and reporting projects",
        )
    return False, "Forbidden Error"


def can_update_project_reports(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"
    if project.status != INVOICING_AND_REPORTING:
        return (
            False,
            "Report Config can be changed only in Invoicing and reporting state",
        )
    if user.is_apply_staff or user == project.user:
        return (
            True,
            "Only Staff and project owner can update report config for Invoicing and reporting projects",
        )
    return False, "Forbidden Error"


def can_view_report(user, report, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"
    if report.project.status not in [COMPLETE, CLOSING, INVOICING_AND_REPORTING]:
        return False, "Report are not available at this state"
    if not report.current:
        return False, "Only current reports can be viewed"
    if report.skipped:
        return False, "Skipped reports are not available"
    if user.is_apply_staff or user.is_finance or user == report.project.user:
        return True, "Staff, Finance, and Project owner can view the report"
    return False, "Forbidden Error"


def can_access_project(user, project):
    if not user.is_authenticated:
        return False, "Login Required"

    if user.is_apply_staff or user.is_finance or user.is_contracting:
        # Staff, Finance and Contracting are internal and trusted peoples,
        # Their action are limited, but they can view all projects.
        return True, "Staff, Finance and Contracting can view project in all statuses"

    if user.is_applicant and user == project.user:
        return True, "Vendor(project user) can view project in all statuses"

    if (
        project.status in [DRAFT, INTERNAL_APPROVAL, CONTRACTING]
        and project.paf_approvals.exists()
    ):
        paf_reviewer_roles_users_ids = []
        for approval in project.paf_approvals.all():
            paf_reviewer_roles_users_ids.extend(
                [
                    role_user.id
                    for role_user in get_users_for_groups(
                        list(approval.paf_reviewer_role.user_roles.all()),
                        exact_match=True,
                    )
                ]
            )
        if user.id in paf_reviewer_roles_users_ids:
            return (
                True,
                "PAF Approvers can access the project in Draft, Approval state and after approval state",
            )

    return False, "Forbidden Error"


permissions_map = {
    "contract_approve": can_approve_contract,
    "contract_upload": can_upload_contract,
    "paf_status_update": can_update_paf_status,
    "paf_approvers_update": can_update_paf_approvers,
    "paf_approvers_assign": can_assign_paf_approvers,
    "update_paf_assigned_approvers": can_update_assigned_paf_approvers,  # Permission for UpdateAssignApproversView
    "project_status_update": can_update_project_status,
    "project_reports_update": can_update_project_reports,
    "report_update": can_update_report,
    "report_config_update": can_update_report_config,
    "report_view": can_view_report,
    "submit_contract_documents": can_submit_contract_documents,
    "project_access": can_access_project,
}
