"""
Tests for hypha/apply/projects/permissions.py

Coverage targets (all previously untested):
  - can_approve_contract
  - can_upload_contract  (co-applicant paths + STAFF_UPLOAD_CONTRACT)
  - can_submit_contract_documents
  - can_update_project_status
  - can_access_project
  - can_edit_paf
  - can_view_contract_category_documents
  - PAF approval functions (can_update_paf_approvers, can_update_assigned_paf_approvers,
                            can_assign_paf_approvers, can_update_paf_status)
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings

from hypha.apply.funds.models.co_applicants import (
    CoApplicant,
    CoApplicantInvite,
    CoApplicantInviteStatus,
    CoApplicantProjectPermission,
    CoApplicantRole,
)
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ApproverFactory,
    ContractingFactory,
    FinanceFactory,
    StaffFactory,
    SuperUserFactory,
)

from ..models.project import (
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
)
from ..permissions import (
    can_access_project,
    can_approve_contract,
    can_assign_paf_approvers,
    can_edit_paf,
    can_submit_contract_documents,
    can_update_assigned_paf_approvers,
    can_update_paf_approvers,
    can_update_paf_status,
    can_update_project_status,
    can_upload_contract,
    can_view_contract_category_documents,
)
from .factories import (
    ContractFactory,
    PAFApprovalsFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
    ProjectSettingsFactory,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_co_applicant(project, user, role=CoApplicantRole.EDIT, permissions=None):
    """Create a CoApplicant linked to the project's submission."""
    if permissions is None:
        permissions = []
    invite = CoApplicantInvite.objects.create(
        submission=project.submission,
        invited_user_email=user.email,
        status=CoApplicantInviteStatus.ACCEPTED,
        role=role,
        project_permission=permissions,
    )
    return CoApplicant.objects.create(
        submission=project.submission,
        user=user,
        invite=invite,
        role=role,
        project_permission=permissions,
    )


def make_request(user=None):
    """Return a minimal GET request carrying the apply site."""
    from wagtail.models import Site

    from hypha.home.factories import ApplySiteFactory

    ApplySiteFactory()
    site = Site.objects.filter(is_default_site=True).first()
    request = RequestFactory().get("/")
    request.user = user or AnonymousUser()
    request.site = site
    return request


def mock_sequential_settings():
    """Return a mock ProjectSettings with sequential PAF approval."""
    settings = MagicMock()
    settings.paf_approval_sequential = True
    return settings


def mock_parallel_settings():
    """Return a mock ProjectSettings with parallel PAF approval."""
    settings = MagicMock()
    settings.paf_approval_sequential = False
    return settings


# ---------------------------------------------------------------------------
# can_approve_contract
# ---------------------------------------------------------------------------


class TestCanApproveContract(TestCase):
    def setUp(self):
        self.project = ProjectFactory(
            status=CONTRACTING, submitted_contract_documents=True
        )
        self.staff = StaffFactory()
        self.applicant = ApplicantFactory()

    def test_staff_can_approve_when_docs_submitted(self):
        ok, _ = can_approve_contract(self.staff, self.project)
        self.assertTrue(ok)

    def test_wrong_status_blocks_approval(self):
        self.project.status = DRAFT
        ok, _ = can_approve_contract(self.staff, self.project)
        self.assertFalse(ok)

    def test_no_submitted_docs_blocks_approval(self):
        self.project.submitted_contract_documents = False
        ok, _ = can_approve_contract(self.staff, self.project)
        self.assertFalse(ok)

    def test_applicant_cannot_approve(self):
        ok, _ = can_approve_contract(self.applicant, self.project)
        self.assertFalse(ok)

    def test_unauthenticated_cannot_approve(self):
        ok, _ = can_approve_contract(AnonymousUser(), self.project)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# can_upload_contract
# ---------------------------------------------------------------------------


class TestCanUploadContract(TestCase):
    def setUp(self):
        self.owner = ApplicantFactory()
        self.project = ProjectFactory(status=CONTRACTING, user=self.owner)
        self.contracting = ContractingFactory()
        self.staff = StaffFactory()

    def test_wrong_status_blocks_upload(self):
        self.project.status = DRAFT
        ok, _ = can_upload_contract(self.owner, self.project)
        self.assertFalse(ok)

    def test_owner_can_upload_when_contract_exists(self):
        ContractFactory(project=self.project)
        ok, _ = can_upload_contract(self.owner, self.project)
        self.assertTrue(ok)

    def test_owner_cannot_upload_without_existing_contract(self):
        # No contract yet — applicant cannot do the initial upload
        ok, _ = can_upload_contract(self.owner, self.project)
        self.assertFalse(ok)

    def test_contracting_user_can_upload(self):
        ok, _ = can_upload_contract(self.contracting, self.project)
        self.assertTrue(ok)

    def test_staff_cannot_upload_by_default(self):
        ok, _ = can_upload_contract(self.staff, self.project)
        self.assertFalse(ok)

    @override_settings(STAFF_UPLOAD_CONTRACT=True)
    def test_staff_can_upload_when_setting_enabled(self):
        ok, _ = can_upload_contract(self.staff, self.project)
        self.assertTrue(ok)

    def test_co_applicant_with_permission_and_edit_role_can_upload(self):
        ContractFactory(project=self.project)
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project,
            co_user,
            role=CoApplicantRole.EDIT,
            permissions=[CoApplicantProjectPermission.CONTRACTING_DOCUMENT],
        )
        ok, _ = can_upload_contract(co_user, self.project)
        self.assertTrue(ok)

    def test_co_applicant_with_view_role_cannot_upload(self):
        ContractFactory(project=self.project)
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project,
            co_user,
            role=CoApplicantRole.VIEW,
            permissions=[CoApplicantProjectPermission.CONTRACTING_DOCUMENT],
        )
        ok, _ = can_upload_contract(co_user, self.project)
        self.assertFalse(ok)

    def test_co_applicant_without_contracting_permission_cannot_upload(self):
        ContractFactory(project=self.project)
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project,
            co_user,
            role=CoApplicantRole.EDIT,
            permissions=[],
        )
        ok, _ = can_upload_contract(co_user, self.project)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# can_submit_contract_documents
# ---------------------------------------------------------------------------


class TestCanSubmitContractDocuments(TestCase):
    def setUp(self):
        self.owner = ApplicantFactory()
        self.project = ProjectFactory(
            status=CONTRACTING, submitted_contract_documents=False, user=self.owner
        )
        self.contract = ContractFactory(project=self.project)
        self.staff = StaffFactory()

    def test_wrong_status_blocks_submission(self):
        self.project.status = DRAFT
        ok, _ = can_submit_contract_documents(
            self.owner, self.project, contract=self.contract
        )
        self.assertFalse(ok)

    def test_non_applicant_cannot_submit(self):
        ok, _ = can_submit_contract_documents(
            self.staff, self.project, contract=self.contract
        )
        self.assertFalse(ok)

    def test_owner_can_submit_when_docs_not_yet_submitted(self):
        ok, _ = can_submit_contract_documents(
            self.owner, self.project, contract=self.contract
        )
        self.assertTrue(ok)

    def test_owner_cannot_submit_when_docs_already_submitted(self):
        self.project.submitted_contract_documents = True
        ok, _ = can_submit_contract_documents(
            self.owner, self.project, contract=self.contract
        )
        self.assertFalse(ok)

    def test_missing_contract_kwarg_blocks_submission(self):
        ok, _ = can_submit_contract_documents(self.owner, self.project)
        self.assertFalse(ok)

    def test_co_applicant_with_permission_and_edit_can_submit(self):
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project,
            co_user,
            role=CoApplicantRole.EDIT,
            permissions=[CoApplicantProjectPermission.CONTRACTING_DOCUMENT],
        )
        ok, _ = can_submit_contract_documents(
            co_user, self.project, contract=self.contract
        )
        self.assertTrue(ok)

    def test_co_applicant_without_permission_cannot_submit(self):
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project, co_user, role=CoApplicantRole.EDIT, permissions=[]
        )
        ok, _ = can_submit_contract_documents(
            co_user, self.project, contract=self.contract
        )
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# can_update_project_status
# ---------------------------------------------------------------------------


class TestCanUpdateProjectStatus(TestCase):
    def setUp(self):
        self.staff = StaffFactory()
        self.applicant = ApplicantFactory()

    def test_staff_can_update_from_invoicing_and_reporting(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ok, _ = can_update_project_status(self.staff, project)
        self.assertTrue(ok)

    def test_staff_can_update_from_draft_when_no_paf_roles(self):
        # No PAFReviewersRole rows → no_pafreviewer_role() returns True
        project = ProjectFactory(status=DRAFT)
        ok, _ = can_update_project_status(self.staff, project)
        self.assertTrue(ok)

    def test_staff_cannot_update_draft_when_paf_roles_exist(self):
        project = ProjectFactory(status=DRAFT)
        PAFReviewerRoleFactory()  # creates a PAFReviewersRole row
        ok, _ = can_update_project_status(self.staff, project)
        self.assertFalse(ok)

    def test_applicant_cannot_update_status(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ok, _ = can_update_project_status(self.applicant, project)
        self.assertFalse(ok)

    def test_blocked_in_internal_approval_status(self):
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        ok, _ = can_update_project_status(self.staff, project)
        self.assertFalse(ok)

    def test_blocked_in_contracting_status(self):
        project = ProjectFactory(status=CONTRACTING)
        ok, _ = can_update_project_status(self.staff, project)
        self.assertFalse(ok)

    def test_unauthenticated_cannot_update(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ok, _ = can_update_project_status(AnonymousUser(), project)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# can_access_project
# ---------------------------------------------------------------------------


class TestCanAccessProject(TestCase):
    def setUp(self):
        self.owner = ApplicantFactory()
        self.project = ProjectFactory(user=self.owner)

    def test_staff_can_access(self):
        ok, _ = can_access_project(StaffFactory(), self.project)
        self.assertTrue(ok)

    def test_finance_can_access(self):
        ok, _ = can_access_project(FinanceFactory(), self.project)
        self.assertTrue(ok)

    def test_contracting_can_access(self):
        ok, _ = can_access_project(ContractingFactory(), self.project)
        self.assertTrue(ok)

    def test_project_owner_can_access(self):
        ok, _ = can_access_project(self.owner, self.project)
        self.assertTrue(ok)

    def test_unrelated_applicant_cannot_access(self):
        other = ApplicantFactory()
        ok, _ = can_access_project(other, self.project)
        self.assertFalse(ok)

    def test_unauthenticated_cannot_access(self):
        ok, _ = can_access_project(AnonymousUser(), self.project)
        self.assertFalse(ok)

    def test_co_applicant_with_project_permission_can_access(self):
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project,
            co_user,
            permissions=[CoApplicantProjectPermission.CONTRACTING_DOCUMENT],
        )
        ok, _ = can_access_project(co_user, self.project)
        self.assertTrue(ok)

    def test_co_applicant_without_project_permission_cannot_access(self):
        co_user = ApplicantFactory()
        make_co_applicant(self.project, co_user, permissions=[])
        ok, _ = can_access_project(co_user, self.project)
        self.assertFalse(ok)

    def test_paf_reviewer_can_access_in_internal_approval(self):
        self.project.status = INTERNAL_APPROVAL
        self.project.save()
        approver = StaffFactory()
        PAFApprovalsFactory(project=self.project, user=approver)
        ok, _ = can_access_project(approver, self.project)
        self.assertTrue(ok)

    def test_paf_reviewer_cannot_access_in_invoicing_status(self):
        from django.contrib.auth.models import Group

        from hypha.apply.projects.models.project import PAFApprovals, PAFReviewersRole
        from hypha.apply.users.roles import APPROVER_GROUP_NAME

        self.project.status = INVOICING_AND_REPORTING
        self.project.save()

        # Non-staff user in only the Approver group
        approver_group = Group.objects.get(name=APPROVER_GROUP_NAME)
        approver = ApplicantFactory()
        approver.groups.set([approver_group])

        # PAF role that requires only Approver group
        role = PAFReviewersRole.objects.create(
            label="Approver Only Role", page=ProjectSettingsFactory()
        )
        role.user_roles.set([approver_group])
        PAFApprovals.objects.create(
            project=self.project, paf_reviewer_role=role, user=approver
        )

        ok, _ = can_access_project(approver, self.project)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# can_edit_paf
# ---------------------------------------------------------------------------


class TestCanEditPaf(TestCase):
    def test_editable_when_no_paf_roles_and_project_not_complete(self):
        project = ProjectFactory(status=DRAFT)
        # No PAFReviewersRole rows in DB → no_pafreviewer_role() is True
        ok, _ = can_edit_paf(StaffFactory(), project)
        self.assertTrue(ok)

    def test_not_editable_when_no_paf_roles_but_project_complete(self):
        from ..models.project import COMPLETE

        project = ProjectFactory(status=COMPLETE)
        ok, _ = can_edit_paf(StaffFactory(), project)
        self.assertFalse(ok)

    def test_editable_when_user_can_edit_via_editable_by(self):
        PAFReviewerRoleFactory()  # ensure no_pafreviewer_role() is False
        project = ProjectFactory(status=DRAFT)
        # project.editable_by(lead) returns True for the lead
        ok, _ = can_edit_paf(project.lead, project)
        self.assertTrue(ok)

    def test_not_editable_when_paf_roles_exist_and_wrong_user(self):
        PAFReviewerRoleFactory()
        project = ProjectFactory(status=DRAFT)
        # Non-lead, non-staff user — editable_by() returns False for them
        unrelated = ApplicantFactory()
        ok, _ = can_edit_paf(unrelated, project)
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# can_view_contract_category_documents
# ---------------------------------------------------------------------------


class TestCanViewContractCategoryDocuments(TestCase):
    def setUp(self):
        self.project = ProjectFactory()

    def test_superuser_can_view(self):
        ok, _ = can_view_contract_category_documents(SuperUserFactory(), self.project)
        self.assertTrue(ok)

    def test_project_owner_can_view(self):
        ok, _ = can_view_contract_category_documents(self.project.user, self.project)
        self.assertTrue(ok)

    def test_co_applicant_with_contracting_permission_can_view(self):
        co_user = ApplicantFactory()
        make_co_applicant(
            self.project,
            co_user,
            permissions=[CoApplicantProjectPermission.CONTRACTING_DOCUMENT],
        )
        ok, _ = can_view_contract_category_documents(co_user, self.project)
        self.assertTrue(ok)

    def test_co_applicant_without_contracting_permission_cannot_view(self):
        co_user = ApplicantFactory()
        make_co_applicant(self.project, co_user, permissions=[])
        ok, _ = can_view_contract_category_documents(co_user, self.project)
        self.assertFalse(ok)

    def test_returns_false_without_contract_category_kwarg(self):
        ok, _ = can_view_contract_category_documents(StaffFactory(), self.project)
        self.assertFalse(ok)

    def test_user_in_document_access_group_can_view(self):
        from django.contrib.auth.models import Group

        from hypha.apply.projects.models.project import ContractDocumentCategory

        group = Group.objects.create(name="doc-reviewers")
        staff = StaffFactory()
        staff.groups.add(group)
        category = ContractDocumentCategory.objects.create(
            name="Test Category", recommended_minimum=1
        )
        category.document_access_view.add(group)

        ok, _ = can_view_contract_category_documents(
            staff, self.project, contract_category=category
        )
        self.assertTrue(ok)

    def test_user_not_in_document_access_group_cannot_view(self):
        from django.contrib.auth.models import Group

        from hypha.apply.projects.models.project import ContractDocumentCategory

        group = Group.objects.create(name="restricted-reviewers")
        category = ContractDocumentCategory.objects.create(
            name="Restricted Category", recommended_minimum=1
        )
        category.document_access_view.add(group)

        ok, _ = can_view_contract_category_documents(
            StaffFactory(), self.project, contract_category=category
        )
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# PAF approval functions
# ---------------------------------------------------------------------------


class TestCanUpdatePafApprovers(TestCase):
    def setUp(self):
        self.project = ProjectFactory(status=INTERNAL_APPROVAL)

    def test_project_lead_can_always_update(self):
        ok, _ = can_update_paf_approvers(self.project.lead, self.project)
        self.assertTrue(ok)

    def test_unauthenticated_cannot_update(self):
        ok, _ = can_update_paf_approvers(AnonymousUser(), self.project)
        self.assertFalse(ok)

    def test_wrong_status_blocks_update(self):
        self.project.status = DRAFT
        ok, _ = can_update_paf_approvers(self.project.lead, self.project)
        self.assertFalse(ok)

    def test_no_paf_approvals_blocks_non_lead(self):
        staff = StaffFactory()
        ok, _ = can_update_paf_approvers(staff, self.project)
        self.assertFalse(ok)

    def test_sequential_reviewer_with_assigned_user_can_update(self):
        approver = ApproverFactory()
        approval = PAFApprovalsFactory(  # noqa: F841
            project=self.project, user=approver, approved=False
        )
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_sequential_settings(),
        ):
            ok, _ = can_update_paf_approvers(approver, self.project, request=request)
        self.assertTrue(ok)

    def test_parallel_reviewer_can_update_any_unapproved(self):
        approver = ApproverFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_parallel_settings(),
        ):
            ok, _ = can_update_paf_approvers(approver, self.project, request=request)
        self.assertTrue(ok)


class TestCanAssignPafApprovers(TestCase):
    def setUp(self):
        self.project = ProjectFactory(status=INTERNAL_APPROVAL)

    def test_unauthenticated_cannot_assign(self):
        ok, _ = can_assign_paf_approvers(AnonymousUser(), self.project)
        self.assertFalse(ok)

    def test_wrong_status_blocks_assignment(self):
        self.project.status = DRAFT
        ok, _ = can_assign_paf_approvers(StaffFactory(), self.project)
        self.assertFalse(ok)

    def test_no_paf_approvals_blocks_assignment(self):
        ok, _ = can_assign_paf_approvers(StaffFactory(), self.project)
        self.assertFalse(ok)

    def test_sequential_slot_already_assigned_blocks_assignment(self):
        approver = StaffFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_sequential_settings(),
        ):
            ok, _ = can_assign_paf_approvers(approver, self.project, request=request)
        # user is already assigned — should be blocked
        self.assertFalse(ok)

    def test_sequential_empty_slot_allows_assignment(self):
        approver = StaffFactory()
        # Create approval with NO user (empty slot)
        approval = PAFApprovalsFactory(project=self.project, user=None, approved=False)
        approval.user = None
        approval.save()
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_sequential_settings(),
        ):
            ok, _ = can_assign_paf_approvers(approver, self.project, request=request)
        self.assertTrue(ok)

    def test_parallel_empty_slot_allows_assignment(self):
        approver = StaffFactory()
        approval = PAFApprovalsFactory(project=self.project, user=None, approved=False)
        approval.user = None
        approval.save()
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_parallel_settings(),
        ):
            ok, _ = can_assign_paf_approvers(approver, self.project, request=request)
        self.assertTrue(ok)


class TestCanUpdatePafStatus(TestCase):
    def setUp(self):
        self.project = ProjectFactory(status=INTERNAL_APPROVAL)

    def test_unauthenticated_cannot_update(self):
        request = make_request(AnonymousUser())
        ok, _ = can_update_paf_status(AnonymousUser(), self.project, request=request)
        self.assertFalse(ok)

    def test_no_unapproved_approvals_blocks_update(self):
        approver = StaffFactory()
        request = make_request(approver)
        # No PAFApprovals exist → filter(approved=False) is empty
        ok, _ = can_update_paf_status(approver, self.project, request=request)
        self.assertFalse(ok)

    def test_wrong_status_blocks_update(self):
        self.project.status = DRAFT
        self.project.save()
        approver = StaffFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        ok, _ = can_update_paf_status(approver, self.project, request=request)
        self.assertFalse(ok)

    def test_sequential_reviewer_in_next_role_can_update(self):
        approver = ApproverFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_sequential_settings(),
        ):
            ok, _ = can_update_paf_status(approver, self.project, request=request)
        self.assertTrue(ok)

    def test_parallel_reviewer_can_update(self):
        approver = ApproverFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_parallel_settings(),
        ):
            ok, _ = can_update_paf_status(approver, self.project, request=request)
        self.assertTrue(ok)

    def test_unrelated_user_cannot_update_status(self):
        approver = StaffFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        unrelated = ApplicantFactory()
        request = make_request(unrelated)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_sequential_settings(),
        ):
            ok, _ = can_update_paf_status(unrelated, self.project, request=request)
        self.assertFalse(ok)


class TestCanUpdateAssignedPafApprovers(TestCase):
    def setUp(self):
        self.project = ProjectFactory(status=INTERNAL_APPROVAL)

    def test_unauthenticated_cannot_update(self):
        ok, _ = can_update_assigned_paf_approvers(AnonymousUser(), self.project)
        self.assertFalse(ok)

    def test_wrong_status_blocks(self):
        self.project.status = DRAFT
        ok, _ = can_update_assigned_paf_approvers(StaffFactory(), self.project)
        self.assertFalse(ok)

    def test_no_paf_approvals_blocks(self):
        ok, _ = can_update_assigned_paf_approvers(StaffFactory(), self.project)
        self.assertFalse(ok)

    def test_sequential_reviewer_in_next_role_can_update(self):
        approver = ApproverFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_sequential_settings(),
        ):
            ok, _ = can_update_assigned_paf_approvers(
                approver, self.project, request=request
            )
        self.assertTrue(ok)

    def test_parallel_reviewer_can_update_any_unapproved(self):
        approver = ApproverFactory()
        PAFApprovalsFactory(project=self.project, user=approver, approved=False)
        request = make_request(approver)
        with patch(
            "hypha.apply.projects.permissions.ProjectSettings.for_request",
            return_value=mock_parallel_settings(),
        ):
            ok, _ = can_update_assigned_paf_approvers(
                approver, self.project, request=request
            )
        self.assertTrue(ok)
