"""Tests for projects/templatetags/project_tags.py."""

from django.test import TestCase, override_settings

from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ContractingFactory,
    FinanceFactory,
    StaffFactory,
    UserFactory,
)

from ..models.project import (
    CLOSING,
    COMPLETE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
)
from ..templatetags.project_tags import (
    allow_collapsible_header,
    can_access_supporting_documents_section,
    display_project_status,
    project_can_have_contracting_section,
    project_show_reports_section,
    show_closing_banner,
    show_start_date,
    user_can_remove_supporting_documents,
    user_can_skip_pafapproval_process,
    user_can_take_actions,
    user_next_step_instructions,
)
from .factories import (
    ContractFactory,
    PAFApprovalsFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
)

ALL_STATUSES = [
    DRAFT,
    INTERNAL_APPROVAL,
    CONTRACTING,
    INVOICING_AND_REPORTING,
    CLOSING,
    COMPLETE,
]


class TestProjectShowReportsSection(TestCase):
    def test_true_for_invoicing_and_reporting(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        self.assertTrue(project_show_reports_section(project))

    def test_true_for_closing(self):
        project = ProjectFactory(status=CLOSING)
        self.assertTrue(project_show_reports_section(project))

    def test_true_for_complete(self):
        project = ProjectFactory(status=COMPLETE)
        self.assertTrue(project_show_reports_section(project))

    def test_false_for_draft(self):
        self.assertFalse(project_show_reports_section(ProjectFactory(status=DRAFT)))

    def test_false_for_contracting(self):
        self.assertFalse(
            project_show_reports_section(ProjectFactory(status=CONTRACTING))
        )

    def test_false_for_internal_approval(self):
        self.assertFalse(
            project_show_reports_section(ProjectFactory(status=INTERNAL_APPROVAL))
        )


class TestProjectCanHaveContractingSection(TestCase):
    def test_false_for_draft(self):
        self.assertFalse(
            project_can_have_contracting_section(ProjectFactory(status=DRAFT))
        )

    def test_false_for_internal_approval(self):
        self.assertFalse(
            project_can_have_contracting_section(
                ProjectFactory(status=INTERNAL_APPROVAL)
            )
        )

    def test_true_for_contracting(self):
        self.assertTrue(
            project_can_have_contracting_section(ProjectFactory(status=CONTRACTING))
        )

    def test_true_for_invoicing_and_reporting(self):
        self.assertTrue(
            project_can_have_contracting_section(
                ProjectFactory(status=INVOICING_AND_REPORTING)
            )
        )

    def test_true_for_closing(self):
        self.assertTrue(
            project_can_have_contracting_section(ProjectFactory(status=CLOSING))
        )

    def test_true_for_complete(self):
        self.assertTrue(
            project_can_have_contracting_section(ProjectFactory(status=COMPLETE))
        )


class TestCanAccessSupportingDocumentsSection(TestCase):
    def test_true_for_draft(self):
        self.assertTrue(
            can_access_supporting_documents_section(ProjectFactory(status=DRAFT))
        )

    def test_true_for_contracting(self):
        self.assertTrue(
            can_access_supporting_documents_section(ProjectFactory(status=CONTRACTING))
        )

    def test_false_for_invoicing_and_reporting(self):
        self.assertFalse(
            can_access_supporting_documents_section(
                ProjectFactory(status=INVOICING_AND_REPORTING)
            )
        )

    def test_false_for_closing(self):
        self.assertFalse(
            can_access_supporting_documents_section(ProjectFactory(status=CLOSING))
        )

    def test_false_for_complete(self):
        self.assertFalse(
            can_access_supporting_documents_section(ProjectFactory(status=COMPLETE))
        )


class TestShowClosingBanner(TestCase):
    def test_true_for_complete(self):
        self.assertTrue(show_closing_banner(ProjectFactory(status=COMPLETE)))

    def test_true_for_closing(self):
        self.assertTrue(show_closing_banner(ProjectFactory(status=CLOSING)))

    def test_false_for_draft(self):
        self.assertFalse(show_closing_banner(ProjectFactory(status=DRAFT)))

    def test_false_for_contracting(self):
        self.assertFalse(show_closing_banner(ProjectFactory(status=CONTRACTING)))

    def test_false_for_invoicing_and_reporting(self):
        self.assertFalse(
            show_closing_banner(ProjectFactory(status=INVOICING_AND_REPORTING))
        )


class TestDisplayProjectStatus(TestCase):
    def setUp(self):
        self.project = ProjectFactory(status=INVOICING_AND_REPORTING)

    def test_staff_sees_internal_status(self):
        staff = StaffFactory()
        result = display_project_status(self.project, staff)
        self.assertEqual(result, self.project.status_display)

    def test_finance_sees_internal_status(self):
        finance = FinanceFactory()
        result = display_project_status(self.project, finance)
        self.assertEqual(result, self.project.status_display)

    def test_contracting_sees_internal_status(self):
        contracting = ContractingFactory()
        result = display_project_status(self.project, contracting)
        self.assertEqual(result, self.project.status_display)

    def test_applicant_sees_public_status(self):
        # INTERNAL_APPROVAL has a public display of "{ORG_SHORT_NAME} approval"
        # which is different from its internal status_display "Internal approval"
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        applicant = ApplicantFactory()
        result = display_project_status(project, applicant)
        self.assertNotEqual(result, project.status_display)


class TestShowStartDate(TestCase):
    @override_settings(PROJECTS_START_AFTER_CONTRACTING=False)
    def test_always_true_when_setting_disabled(self):
        for status in ALL_STATUSES:
            self.assertTrue(show_start_date(ProjectFactory(status=status)))

    @override_settings(PROJECTS_START_AFTER_CONTRACTING=True)
    def test_true_for_invoicing_and_reporting_when_setting_enabled(self):
        self.assertTrue(show_start_date(ProjectFactory(status=INVOICING_AND_REPORTING)))

    @override_settings(PROJECTS_START_AFTER_CONTRACTING=True)
    def test_true_for_closing_when_setting_enabled(self):
        self.assertTrue(show_start_date(ProjectFactory(status=CLOSING)))

    @override_settings(PROJECTS_START_AFTER_CONTRACTING=True)
    def test_true_for_complete_when_setting_enabled(self):
        self.assertTrue(show_start_date(ProjectFactory(status=COMPLETE)))

    @override_settings(PROJECTS_START_AFTER_CONTRACTING=True)
    def test_false_for_draft_when_setting_enabled(self):
        self.assertFalse(show_start_date(ProjectFactory(status=DRAFT)))

    @override_settings(PROJECTS_START_AFTER_CONTRACTING=True)
    def test_false_for_contracting_when_setting_enabled(self):
        self.assertFalse(show_start_date(ProjectFactory(status=CONTRACTING)))


class TestAllowCollapsibleHeader(TestCase):
    def test_project_documents_collapsible_after_draft_and_internal_approval(self):
        self.assertFalse(
            allow_collapsible_header(ProjectFactory(status=DRAFT), "project_documents")
        )
        self.assertFalse(
            allow_collapsible_header(
                ProjectFactory(status=INTERNAL_APPROVAL), "project_documents"
            )
        )
        self.assertTrue(
            allow_collapsible_header(
                ProjectFactory(status=CONTRACTING), "project_documents"
            )
        )

    def test_contracting_documents_collapsible_after_contracting(self):
        self.assertFalse(
            allow_collapsible_header(
                ProjectFactory(status=DRAFT), "contracting_documents"
            )
        )
        self.assertFalse(
            allow_collapsible_header(
                ProjectFactory(status=CONTRACTING), "contracting_documents"
            )
        )
        self.assertTrue(
            allow_collapsible_header(
                ProjectFactory(status=INVOICING_AND_REPORTING), "contracting_documents"
            )
        )

    def test_unknown_header_type_returns_false(self):
        for status in ALL_STATUSES:
            self.assertFalse(
                allow_collapsible_header(ProjectFactory(status=status), "unknown")
            )


class TestUserCanRemoveSupportingDocuments(TestCase):
    def test_staff_can_remove_in_draft(self):
        staff = StaffFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertTrue(user_can_remove_supporting_documents(project, staff))

    def test_staff_cannot_remove_outside_draft(self):
        staff = StaffFactory()
        for status in [CONTRACTING, INVOICING_AND_REPORTING, CLOSING, COMPLETE]:
            self.assertFalse(
                user_can_remove_supporting_documents(
                    ProjectFactory(status=status), staff
                )
            )

    def test_applicant_cannot_remove(self):
        applicant = ApplicantFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertFalse(user_can_remove_supporting_documents(project, applicant))


class TestUserCanTakeActions(TestCase):
    def test_staff_can_take_actions(self):
        staff = StaffFactory()
        project = ProjectFactory()
        self.assertTrue(user_can_take_actions(project, staff))

    def test_contracting_can_take_actions(self):
        contracting = ContractingFactory()
        project = ProjectFactory()
        self.assertTrue(user_can_take_actions(project, contracting))

    def test_paf_approver_can_take_actions(self):
        staff = StaffFactory()
        project = ProjectFactory()
        PAFApprovalsFactory(project=project, user=staff)
        self.assertTrue(user_can_take_actions(project, staff))

    def test_applicant_cannot_take_actions(self):
        applicant = ApplicantFactory()
        project = ProjectFactory()
        self.assertFalse(user_can_take_actions(project, applicant))

    def test_unrelated_user_cannot_take_actions(self):
        user = UserFactory()
        project = ProjectFactory()
        self.assertFalse(user_can_take_actions(project, user))


class TestUserCanSkipPafApprovalProcess(TestCase):
    def test_staff_in_draft_with_no_paf_roles_can_skip(self):
        staff = StaffFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertTrue(user_can_skip_pafapproval_process(project, staff))

    def test_staff_in_draft_with_paf_roles_cannot_skip(self):
        PAFReviewerRoleFactory()
        staff = StaffFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertFalse(user_can_skip_pafapproval_process(project, staff))

    def test_staff_not_in_draft_cannot_skip(self):
        staff = StaffFactory()
        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(user_can_skip_pafapproval_process(project, staff))

    def test_applicant_cannot_skip(self):
        applicant = ApplicantFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertFalse(user_can_skip_pafapproval_process(project, applicant))


class TestUserNextStepInstructions(TestCase):
    def test_returns_instructions_for_owner_when_contract_not_signed(self):
        applicant = ApplicantFactory()
        project = ProjectFactory(status=CONTRACTING, user=applicant)
        # Contract uploaded but NOT signed by applicant
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        result = user_next_step_instructions(project, applicant)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_returns_false_when_no_contract(self):
        applicant = ApplicantFactory()
        project = ProjectFactory(status=CONTRACTING, user=applicant)
        self.assertFalse(user_next_step_instructions(project, applicant))

    def test_returns_false_for_non_owner(self):
        applicant = ApplicantFactory()
        other_user = ApplicantFactory()
        project = ProjectFactory(status=CONTRACTING, user=applicant)
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        self.assertFalse(user_next_step_instructions(project, other_user))

    def test_returns_false_outside_contracting(self):
        applicant = ApplicantFactory()
        project = ProjectFactory(status=DRAFT, user=applicant)
        self.assertFalse(user_next_step_instructions(project, applicant))
