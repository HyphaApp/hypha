from django.conf import settings
from django.core.exceptions import PermissionDenied
from rolepermissions.permissions import register_object_checker

from hypha.apply.activity.adapters.utils import get_users_for_groups
from hypha.apply.funds.models.co_applicants import (
    CoApplicantProjectPermission,
    CoApplicantRole,
)
from hypha.apply.users.models import User
from hypha.apply.users.roles import Applicant, Staff

from .models.project import (
    CLOSING,
    COMPLETE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
    ProjectSettings,
)
from .utils import no_pafreviewer_role


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

    if user.is_apply_staff and not user.is_applicant:
        return True, "Only Staff can approve the contract"

    return False, "Forbidden Error"


def can_upload_contract(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, "Project is not in Contracting State"

    if not user.is_authenticated:
        return False, "Login Required"

    if user.is_applicant and project.contracts.exists():
        if user == project.user:
            return True, "Project Owner can only re-upload contract with countersigned"
        co_applicant = project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.CONTRACTING_DOCUMENT
            in co_applicant.project_permission
            and co_applicant.role == CoApplicantRole.EDIT
        ):
            return (
                True,
                "Co-applicant with edit permission for project's contracting document can upload contract",
            )
        return False, "Forbidden Error"

    if user.is_contracting:
        return True, "Contracting team can upload the contract"

    if user.is_apply_staff and settings.STAFF_UPLOAD_CONTRACT:
        return True, "Staff can upload contract as set in settings"

    return False, "Forbidden Error"


def can_submit_contract_documents(user, project, **kwargs):
    if project.status != CONTRACTING:
        return False, "Project is not in Contracting State"

    if not user.is_applicant:
        return False, "Only Applicants can submit contracting documents"
    if not kwargs.get("contract", None):
        return False, "Can not submit without contract"
    if not project.submitted_contract_documents:
        if user == project.user:
            return True, "Vendor can submit contracting documents"
        co_applicant = project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.CONTRACTING_DOCUMENT
            in co_applicant.project_permission
            and co_applicant.role == CoApplicantRole.EDIT
        ):
            return (
                True,
                "Co-applicant with edit permission for project's contracting document can submit contracting documents",
            )
        return (
            False,
            "Only applicant and co-applicant with appropriate permission can submit docs",
        )

    return False, "Forbidden Error"


def can_update_paf_approvers(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"

    if project.status != INTERNAL_APPROVAL:
        return (
            False,
            "Project form approvers can be updated only in Internal approval state",
        )
    if user == project.lead:
        return True, "Lead can update approvers in approval state"
    if not project.paf_approvals.exists():
        return (
            False,
            "No user can update approvers without project form approval, except lead (lead can add project form approvals)",
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
                    "Project form reviewer-roles users can update next approval approvers if any approvers assigned",
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
            return True, "Project form reviewer-roles users can update approvers"
    return False, "Forbidden Error"


def can_update_assigned_paf_approvers(user, project, **kwargs):
    """
    Only for Approvers teams members(with PAFReviewerRoles' user_roles' users)
    UpdateAssignApproversView will be used by only approvers teams members.
    """
    if not user.is_authenticated:
        return False, "Login Required"
    if project.status != INTERNAL_APPROVAL:
        return (
            False,
            "Project form approvers can be assigned only in Internal approval state",
        )
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
                return True, "Project form reviewer-roles users can assign approvers"
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
            return True, "Project form reviewer-roles users can assign approvers"
    return False, "Forbidden Error"


def can_assign_paf_approvers(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"

    if project.status != INTERNAL_APPROVAL:
        return (
            False,
            "Project form approvers can be assigned only in Internal approval state",
        )
    if not project.paf_approvals.exists():
        return False, "No user can assign approvers with project form approvals"

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
                    return (
                        True,
                        "Project form reviewer-roles users can assign approvers",
                    )
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
            return True, "Project form reviewer-roles users can assign approvers"
    return False, "Forbidden Error"


def can_update_paf_status(user, project, **kwargs):
    if not user.is_authenticated:
        return False, "Login Required"

    if not project.paf_approvals.filter(approved=False).exists():
        return False, "No project form approvals exists"

    if project.status != INTERNAL_APPROVAL:
        return False, "Incorrect project status to approve project form"

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
                    "Next approval group users can approve project form (for sequential approvals)",
                )
            return (
                False,
                "Only Next approval group can approve project form (for sequential approvals)",
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
                    "All approval group users can approve project form (for parallel approvals)",
                )
            return (
                False,
                "Only approval group users can approve project form (for parallel approvals)",
            )

    return False, "Forbidden Error"


def can_update_project_status(user, project, **kwargs):
    if project.status not in [DRAFT, COMPLETE, CLOSING, INVOICING_AND_REPORTING]:
        return False, "Forbidden Error"

    if not user.is_authenticated:
        return False, "Login Required"

    if user.is_apply_staff or user.is_apply_staff_admin:
        if project.status == DRAFT:
            if no_pafreviewer_role():
                return (
                    True,
                    "Staff and Staff Admin can skip the project form approval process",
                )
        else:
            return True, "Staff and Staff Admin can update status"

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
        user.is_applicant
        and project.submission.co_applicants.filter(user=user).exists()
    ):
        co_applicant = project.submission.co_applicants.filter(user=user).first()
        if co_applicant.project_permission:
            return True, "Co-applicant with project permission can access project"
        return False, "Co-applicant without project permission can't access project"

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
                "Project form approvers can access the project in Draft, Approval state and after approval state",
            )

    return False, "Forbidden Error"


def can_view_contract_category_documents(user, project, **kwargs):
    if user.is_superuser:
        return True, "Superuser can view all documents"
    if user == project.user:
        return True, "Vendor can view all documents"
    if user.is_applicant:
        co_applicant = project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.CONTRACTING_DOCUMENT
            in co_applicant.project_permission
        ):
            return True, "Co-applicant with permissions can view contracting documents"

    contract_category = kwargs.get("contract_category")
    if not contract_category:
        return False, "Contract Category is required"
    allowed_group_users = User.objects.filter(
        groups__name__in=list(contract_category.document_access_view.all())
    )
    if allowed_group_users and user in allowed_group_users:
        return True, "Access allowed"

    return False, "Forbidden Error"


def can_edit_paf(user, project):
    if no_pafreviewer_role() and project.status != COMPLETE:
        return True, "Project form is editable for active projects if no reviewer roles"
    if project.editable_by(user):
        return True, "Project form is editable in Draft by this user"
    return False, "You are not allowed to edit the project at this time"


@register_object_checker()
def upload_project_documents(role, user, project) -> bool:
    if role == Staff:
        return True
    return False


@register_object_checker()
def update_contracting_documents(role, user, project) -> bool:
    if role == Applicant:
        if user == project.user:  # owner
            return True
        co_applicant = project.submission.co_applicants.filter(user=user).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.CONTRACTING_DOCUMENT
            in co_applicant.project_permission
            and co_applicant.role == CoApplicantRole.EDIT
        ):  # co-applicant with permission
            return True

    return False


@register_object_checker()
def add_invoice(role, user, project) -> bool:
    if project.status == INVOICING_AND_REPORTING:
        if role == Staff:
            return True
        if role == Applicant:
            if user == project.user:
                return True
            co_applicant = project.submission.co_applicants.filter(user=user).first()
            if (
                co_applicant
                and CoApplicantProjectPermission.INVOICES
                in co_applicant.project_permission
                and co_applicant.role == CoApplicantRole.EDIT
            ):
                return True
    return False


permissions_map = {
    "contract_approve": can_approve_contract,
    "contract_upload": can_upload_contract,
    "paf_status_update": can_update_paf_status,
    "paf_approvers_update": can_update_paf_approvers,
    "paf_approvers_assign": can_assign_paf_approvers,
    "update_paf_assigned_approvers": can_update_assigned_paf_approvers,  # Permission for UpdateAssignApproversView
    "project_status_update": can_update_project_status,
    "submit_contract_documents": can_submit_contract_documents,
    "project_access": can_access_project,
    "paf_edit": can_edit_paf,
    "view_contract_documents": can_view_contract_category_documents,
}
