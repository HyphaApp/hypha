import decimal
import json
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from hypha.apply.activity.adapters.activity_feed import ActivityAdapter
from hypha.apply.activity.options import MESSAGES
from hypha.apply.activity.tests.factories import ActivityFactory
from hypha.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    LabSubmissionFactory,
)
from hypha.apply.projects.utils import get_invoice_status_display_value
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ApproverFactory,
    ContractingFactory,
    FinanceFactory,
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
    UserFactory,
)
from hypha.apply.utils.testing.tests import BaseViewTestCase
from hypha.home.factories import ApplySiteFactory

from ..forms import SetPendingForm
from ..models.invoice import CHANGES_REQUESTED_BY_STAFF, DECLINED, SUBMITTED
from ..models.project import (
    APPROVE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
    REQUEST_CHANGE,
    ProjectSettings,
)
from ..views.project import ContractsMixin, ProjectDetailApprovalView
from .factories import (
    ContractFactory,
    DisbursementFactory,
    DocumentCategoryFactory,
    InvoiceFactory,
    PacketFileFactory,
    PAFApprovalsFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
    ProjectFormPointerFactory,
    SupportingDocumentFactory,
)

# A boilerplate stream form for Project Report tests below.
FORM_FIELDS = [
    {
        "id": "012a4f29-0882-4b1c-b567-aede1b601d4a",
        "type": "number",
        "value": {
            "required": True,
            "help_text": "",
            "field_label": "How many folks did you reach?",
            "default_value": "",
        },
    }
]


class TestUpdateLeadView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = ApproverFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_update_lead(self):
        project = ProjectFactory()

        new_lead = self.user_factory()
        response = self.post_page(
            project, {"lead": new_lead.id}, view_name="lead_update"
        )
        self.assertEqual(response.status_code, 204)

        project.refresh_from_db()
        self.assertEqual(project.lead, new_lead)

    def test_update_lead_from_none(self):
        project = ProjectFactory(lead=None)

        new_lead = self.user_factory()
        response = self.post_page(
            project,
            {"lead": new_lead.id},
            view_name="lead_update",
        )
        self.assertEqual(response.status_code, 204)

        project.refresh_from_db()
        self.assertEqual(project.lead, new_lead)


class TestSendForApprovalView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def setUp(self):
        super().setUp()
        apply_site = ApplySiteFactory()
        self.project_setting, _ = ProjectSettings.objects.get_or_create(
            site_id=apply_site.id
        )
        self.project_setting.use_settings = True
        self.project_setting.save()
        self.role = PAFReviewerRoleFactory(page=self.project_setting)

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_send_for_approval_fails_when_project_is_locked(self):
        project = ProjectFactory(is_locked=True)

        # The view doesn't have any custom changes when form validation fails
        # so check that directly.
        form = SetPendingForm(instance=project)
        self.assertFalse(form.is_valid())

    def test_send_for_approval_fails_when_project_is_not_in_draft_state(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)

        # The view doesn't have any custom changes when form validation fails
        # so check that directly.
        form = SetPendingForm(instance=project)
        self.assertFalse(form.is_valid())

    def test_send_for_approval_happy_path(self):
        project = ProjectFactory(is_locked=False, status=DRAFT)

        response = self.post_page(project, {}, view_name="submit_project_for_approval")
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertFalse(project.is_locked)
        self.assertEqual(project.status, INTERNAL_APPROVAL)


class TestChangePAFStatusView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = ApproverFactory

    def setUp(self):
        super().setUp()
        apply_site = ApplySiteFactory()
        self.project_setting, _ = ProjectSettings.objects.get_or_create(
            site_id=apply_site.id
        )
        self.project_setting.use_settings = True
        self.project_setting.save()
        self.role = PAFReviewerRoleFactory(page=self.project_setting)

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_unassigned_applicant_cant_update_paf_status(self):
        user = ApplicantFactory()
        self.client.force_login(user=user)
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        PAFApprovalsFactory(
            project=project, user=ApplicantFactory(), paf_reviewer_role=self.role
        )

        response = self.post_page(
            project, {"form-submitted-change_paf_status": "", "paf_status": APPROVE}
        )
        self.assertEqual(response.status_code, 403)

    def test_unassigned_staff_cant_update_paf_status(self):
        user = StaffFactory()
        self.client.force_login(user=user)
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        PAFApprovalsFactory(
            project=project, user=StaffFactory(), paf_reviewer_role=self.role
        )

        response = self.post_page(
            project, {"paf_status": APPROVE}, view_name="update_pafstatus"
        )
        self.assertEqual(response.status_code, 403)

    def test_unassigned_finance_cant_update_paf_status(self):
        user = FinanceFactory()
        self.client.force_login(user=user)
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        PAFApprovalsFactory(
            project=project, user=FinanceFactory(), paf_reviewer_role=self.role
        )

        response = self.post_page(
            project, {"paf_status": APPROVE}, view_name="update_pafstatus"
        )
        self.assertEqual(response.status_code, 403)

    def test_unassigned_contracting_cant_update_paf_status(self):
        user = ContractingFactory()
        self.client.force_login(user=user)
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        PAFApprovalsFactory(
            project=project, user=ContractingFactory(), paf_reviewer_role=self.role
        )

        response = self.post_page(
            project,
            {"paf_status": APPROVE},
            view_name="update_pafstatus",
        )
        self.assertEqual(response.status_code, 403)

    def test_assigned_approvers_can_approve_paf(self):
        # reviewer can be staff, finance or contracting
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        approval = PAFApprovalsFactory(
            project=project, user=self.user, paf_reviewer_role=self.role
        )

        response = self.post_page(
            project,
            {"paf_status": APPROVE},
            view_name="update_pafstatus",
        )

        self.assertEqual(response.status_code, 200)

        approval.refresh_from_db()
        project.refresh_from_db()
        self.assertEqual(self.role.label, approval.paf_reviewer_role.label)
        self.assertTrue(approval.approved)
        self.assertIn(approval, project.paf_approvals.filter(approved=True))

    def test_assigned_approvers_can_reject_paf(self):
        # reviewer can be staff, finance or contracting, or any assigned role
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        approval = PAFApprovalsFactory(
            project=project, user=self.user, paf_reviewer_role=self.role
        )

        response = self.post_page(
            project,
            {"paf_status": REQUEST_CHANGE},
            view_name="update_pafstatus",
        )

        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.status, DRAFT)
        approval.refresh_from_db()
        self.assertEqual(self.role.label, approval.paf_reviewer_role.label)
        self.assertFalse(approval.approved)
        self.assertIn(approval, project.paf_approvals.filter(approved=False))

    def test_activity_renders(self):
        pfp = ProjectFormPointerFactory()
        pf_added_msg = ActivityAdapter.messages[MESSAGES.CREATED_PF].lower()
        ActivityFactory(
            message=pf_added_msg,
            source=pfp.project.submission,
            related_object=pfp,
            user=self.user,
        )
        response = self.client.get(
            reverse(
                "apply:projects:partial-pf-status",
                kwargs={"pk": pfp.project.pk, "pfp_pk": pfp.pk},
            ),
            secure=True,
            follow=True,
        )

        self.assertContains(response, pf_added_msg)


class BaseProjectDetailTestCase(BaseViewTestCase):
    url_name = "funds:projects:{}"
    base_view_name = "detail"

    def get_kwargs(self, instance):
        return {"pk": instance.id}


class TestSubmissionProjectsView(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "funds:submissions:{}"
    base_view_name = "projects"

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_two_projects_route_independently(self):
        submission = ApplicationSubmissionFactory()
        first = ProjectFactory(submission=submission, title="Hardware bucket")
        second = ProjectFactory(submission=submission, title="Travel bucket")
        # project ids must differ from the submission id for this to be meaningful
        self.assertNotEqual(first.pk, second.pk)

        for project in (first, second):
            response = self.client.get(
                reverse(
                    "funds:submissions:project",
                    kwargs={"pk": submission.id, "project_pk": project.pk},
                ),
                secure=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, project.title)

    def test_landing_lists_all_projects(self):
        submission = ApplicationSubmissionFactory()
        ProjectFactory(submission=submission, title="Hardware bucket")
        ProjectFactory(submission=submission, title="Travel bucket")
        response = self.client.get(
            reverse("funds:submissions:projects", kwargs={"pk": submission.id}),
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hardware bucket")
        self.assertContains(response, "Travel bucket")

    def test_single_project_redirects_to_detail(self):
        submission = ApplicationSubmissionFactory()
        project = ProjectFactory(submission=submission)
        response = self.client.get(
            reverse("funds:submissions:projects", kwargs={"pk": submission.id}),
            secure=True,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, project.get_absolute_url())


class TestApplicantProjectDetailView(BaseProjectDetailTestCase):
    user_factory = ApplicantFactory

    def test_has_access(self):
        project = ProjectFactory(user=self.user)
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_doesnt_have_access_to_other_project(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 403)

    def test_lab_project_renders(self):
        project = ProjectFactory(user=self.user, submission=LabSubmissionFactory())
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    @override_settings(HIDE_STAFF_IDENTITY=True)
    def test_applicant_cant_see_hidden_lead(self):
        lead = StaffFactory()
        project = ProjectFactory(user=self.user, lead=lead)
        response = self.get_page(project)
        self.assertNotContains(response, str(lead))

    def test_applicant_can_see_lead(self):
        lead = StaffFactory()
        project = ProjectFactory(user=self.user, lead=lead)
        response = self.get_page(project, view_name="project_lead")
        self.assertContains(response, str(lead))


class TestStaffProjectDetailView(BaseProjectDetailTestCase):
    user_factory = StaffFactory

    def test_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_lab_project_renders(self):
        project = ProjectFactory(submission=LabSubmissionFactory())
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_sibling_projects_listed_in_tab_dropdown(self):
        submission = ApplicationSubmissionFactory()
        project = ProjectFactory(submission=submission, title="Hardware bucket")
        ProjectFactory(submission=submission, title="Travel bucket")

        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)
        # both sibling projects appear in the tab dropdown
        self.assertContains(response, "Hardware bucket")
        self.assertContains(response, "Travel bucket")


class TestFinanceProjectDetailView(BaseProjectDetailTestCase):
    user_factory = FinanceFactory

    def setUp(self):
        super().setUp()
        apply_site = ApplySiteFactory()
        self.project_setting, _ = ProjectSettings.objects.get_or_create(
            site_id=apply_site.id
        )
        self.project_setting.use_settings = True
        self.project_setting.save()
        self.role = PAFReviewerRoleFactory(page=self.project_setting)

    def test_has_access(self):
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_lab_project_renders(self):
        project = ProjectFactory(
            submission=LabSubmissionFactory(), status=INTERNAL_APPROVAL
        )
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)


class TestSuperUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = SuperUserFactory

    def test_has_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)


class TestReviewerUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = ReviewerFactory

    def test_doesnt_have_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 403)


class TestRemoveDocumentView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_remove_document(self):
        project = ProjectFactory()
        document = PacketFileFactory()

        response = self.post_page(
            project,
            {
                "form-submitted-remove_document_form": "",
                "id": document.id,
            },
        )
        project.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(document.pk, project.packet_files.values_list("pk", flat=True))

    def test_remove_non_existent_document(self):
        response = self.post_page(
            ProjectFactory(),
            {
                "form-submitted-remove_document_form": "",
                "id": 1,
            },
        )
        self.assertEqual(response.status_code, 200)


class TestApplicantUploadContractView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_owner_upload_contract(self):
        project = ProjectFactory(status=CONTRACTING, user=self.user)
        ContractFactory(project=project)

        test_doc = BytesIO(b"somebinarydata")
        test_doc.name = "contract.pdf"

        response = self.post_page(
            project,
            {
                "form-submitted-contract_form": "",
                "file": test_doc,
            },
        )
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertTrue(
            project.contracts.order_by("-created_at").first().signed_by_applicant
        )

    def test_non_owner_upload_contract(self):
        project = ProjectFactory(status=CONTRACTING)
        contract_count = project.contracts.count()

        test_doc = BytesIO(b"somebinarydata")
        test_doc.name = "test_contract.pdf"

        response = self.post_page(
            project,
            {
                "form-submitted-contract_form": "",
                "file": test_doc,
            },
        )
        self.assertEqual(response.status_code, 403)

        project.refresh_from_db()
        self.assertEqual(project.contracts.count(), contract_count)


class TestUploadDocumentView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def setUp(self):
        super().setUp()
        self.category = DocumentCategoryFactory()

    def get_kwargs(self, instance):
        return {"pk": instance.id, "category_pk": self.category.id}

    def test_upload_document(self):
        project = ProjectFactory()

        test_doc = BytesIO(b"somebinarydata")
        test_doc.name = "test_document.pdf"

        self.assertEqual(project.packet_files.count(), 0)

        response = self.post_page(
            project,
            {
                "title": "test document",
                "category": self.category.id,
                "document": test_doc,
            },
            view_name="supporting_doc_upload",
        )
        self.assertEqual(response.status_code, 204)

        project.refresh_from_db()

        self.assertEqual(project.packet_files.count(), 1)


class TestContractsMixin(TestCase):
    class DummyView:
        def get_context_data(self):
            return {}

    class DummyContractsView(ContractsMixin, DummyView):
        def __init__(self, project):
            self.project = project

        def get_object(self):
            return self.project

    def test_all_signed_and_approved_contracts_appear(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)

        contracts = self.DummyContractsView(project).get_context_data()["contracts"]

        self.assertEqual(len(contracts), 3)

    def test_mixture_with_latest_signed_returns_no_unsigned(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)

        contracts = self.DummyContractsView(project).get_context_data()["contracts"]

        self.assertEqual(len(contracts), 2)
        for contract in contracts:
            self.assertTrue(contract.signed_by_applicant)

    def test_no_contracts_returns_nothing(self):
        project = ProjectFactory()
        contracts = self.DummyContractsView(project).get_context_data()["contracts"]

        self.assertEqual(len(contracts), 0)

    def test_all_unsigned_and_unapproved_returns_only_latest(self):
        project = ProjectFactory()
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        latest = ContractFactory(
            project=project, signed_by_applicant=False, approver=None
        )

        context = self.DummyContractsView(project).get_context_data()

        contracts = context["contracts"]
        to_approve = context["contract_to_approve"]
        to_sign = context["contract_to_sign"]

        self.assertEqual(len(contracts), 0)
        self.assertEqual(latest, to_sign)
        self.assertIsNone(to_approve)

    def test_all_signed_and_unapproved_returns_latest(self):
        project = ProjectFactory()
        ContractFactory(project=project, signed_by_applicant=True, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=None)
        latest = ContractFactory(
            project=project, signed_by_applicant=True, approver=None
        )

        context = self.DummyContractsView(project).get_context_data()

        contracts = context["contracts"]
        to_approve = context["contract_to_approve"]
        to_sign = context["contract_to_sign"]

        self.assertEqual(len(contracts), 0)
        self.assertEqual(latest, to_approve)
        self.assertIsNone(to_sign)

    def test_mixture_of_both_latest_unsigned_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, signed_by_applicant=True, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        latest = ContractFactory(
            project=project, signed_by_applicant=False, approver=None
        )

        context = self.DummyContractsView(project).get_context_data()

        contracts = context["contracts"]
        to_approve = context["contract_to_approve"]
        to_sign = context["contract_to_sign"]

        self.assertEqual(len(contracts), 2)
        self.assertEqual(latest, to_sign)
        self.assertIsNone(to_approve)

    def test_mixture_of_both_latest_signed_and_unapproved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, signed_by_applicant=True, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        latest = ContractFactory(
            project=project, signed_by_applicant=True, approver=None
        )

        context = self.DummyContractsView(project).get_context_data()

        contracts = context["contracts"]
        to_approve = context["contract_to_approve"]
        to_sign = context["contract_to_sign"]

        self.assertEqual(len(contracts), 2)
        self.assertEqual(latest, to_approve)
        self.assertIsNone(to_sign)

    def test_mixture_of_both_latest_signed_and_approved(self):
        project = ProjectFactory()
        user = StaffFactory()
        ContractFactory(project=project, signed_by_applicant=True, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=False, approver=None)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)
        ContractFactory(project=project, signed_by_applicant=True, approver=user)

        context = self.DummyContractsView(project).get_context_data()

        contracts = context["contracts"]
        to_approve = context["contract_to_approve"]
        to_sign = context["contract_to_sign"]

        self.assertEqual(len(contracts), 3)
        self.assertIsNone(to_approve)
        self.assertIsNone(to_sign)


class TestApproveContractView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_approve_unapproved_contract(self):
        project = ProjectFactory(status=CONTRACTING)
        contract = ContractFactory(
            project=project, signed_by_applicant=True, approver=None
        )

        response = self.post_page(
            project,
            {
                "id": contract.id,
            },
            view_name="contract_approve",
        )
        self.assertEqual(response.status_code, 200)

        contract.refresh_from_db()
        self.assertEqual(contract.approver, self.user)

        project.refresh_from_db()
        self.assertEqual(project.status, INVOICING_AND_REPORTING)

    def test_approve_already_approved_contract(self):
        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        user = StaffFactory()
        contract = ContractFactory(
            project=project, signed_by_applicant=True, approver=user
        )

        response = self.post_page(
            project,
            {
                "form-submitted-approve_contract_form": "",
                "id": contract.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        contract.refresh_from_db()
        self.assertEqual(contract.approver, user)

        project.refresh_from_db()
        self.assertEqual(project.status, INVOICING_AND_REPORTING)

    def test_approve_unsigned_contract(self):
        project = ProjectFactory()
        contract = ContractFactory(
            project=project, signed_by_applicant=False, approver=None
        )

        response = self.post_page(
            project,
            {
                "id": contract.id,
            },
            view_name="contract_approve",
        )
        self.assertEqual(response.status_code, 200)

    def test_attempt_to_approve_non_latest(self):
        project = ProjectFactory()
        contract_attempt = ContractFactory(
            project=project, signed_by_applicant=True, approver=None
        )
        contract_meant = ContractFactory(
            project=project, signed_by_applicant=True, approver=None
        )

        response = self.post_page(
            project,
            {
                "id": contract_attempt.id,
            },
            view_name="contract_approve",
        )
        self.assertEqual(response.status_code, 200)

        contract_attempt.refresh_from_db()
        contract_meant.refresh_from_db()
        self.assertIsNone(contract_attempt.approver)
        self.assertIsNone(contract_meant.approver)


class BasePacketFileViewTestCase(BaseViewTestCase):
    url_name = "funds:projects:{}"
    base_view_name = "document"

    def get_kwargs(self, instance):
        return {
            "pk": instance.project.pk,
            "file_pk": instance.id,
        }


class TestStaffPacketView(BasePacketFileViewTestCase):
    user_factory = StaffFactory

    def test_staff_can_access(self):
        document = PacketFileFactory()
        response = self.get_page(document)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])


class TestUserPacketView(BasePacketFileViewTestCase):
    user_factory = ApplicantFactory

    def test_owner_can_access(self):
        document = PacketFileFactory(project__user=self.user)
        response = self.get_page(document)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_user_can_not_access(self):
        document = PacketFileFactory()
        response = self.get_page(document)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.redirect_chain, [])


class TestAnonPacketView(BasePacketFileViewTestCase):
    user_factory = AnonymousUser

    def test_anonymous_can_not_access(self):
        document = PacketFileFactory()
        response = self.get_page(document)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 1)
        for path, _ in response.redirect_chain:
            self.assertIn(reverse(settings.LOGIN_URL), path)


class TestProjectDetailApprovalView(TestCase):
    def test_staff_only(self):
        factory = RequestFactory()
        project = ProjectFactory()

        request = factory.get(f"/project/{project.pk}")
        request.user = StaffFactory()

        response = ProjectDetailApprovalView.as_view()(request, pk=project.pk)
        self.assertEqual(response.status_code, 200)

        request.user = ApplicantFactory()
        with self.assertRaises(PermissionDenied):
            ProjectDetailApprovalView.as_view()(request, pk=project.pk)


class TestStaffDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 200)

    def test_wrong_project_cant(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": other_project.pk})
        self.assertEqual(response.status_code, 404)

    def test_activity_renders(self):
        invoice = InvoiceFactory()
        vendor = ApplicantFactory()
        invoice_added_msg = ActivityAdapter.messages[MESSAGES.CREATE_INVOICE].lower()
        ActivityFactory(
            message=invoice_added_msg,
            source=invoice.project.submission,
            related_object=invoice,
            user=vendor,
        )
        response = self.client.get(
            reverse(
                "apply:projects:partial-invoice-status",
                kwargs={"pk": invoice.project.pk, "invoice_pk": invoice.pk},
            ),
            secure=True,
            follow=True,
        )

        self.assertContains(response, invoice_added_msg)


class TestFinanceDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = FinanceFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 200)


class TestApplicantDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 200)

    def test_other_cant(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 403)

    def test_activity_renders(self):
        invoice = InvoiceFactory(project__user=self.user)
        invoice_added_msg = ActivityAdapter.messages[MESSAGES.CREATE_INVOICE].lower()
        ActivityFactory(
            message=invoice_added_msg,
            source=invoice.project.submission,
            related_object=invoice,
            user=self.user,
        )
        response = self.client.get(
            reverse(
                "apply:projects:partial-invoice-status",
                kwargs={"pk": invoice.project.pk, "invoice_pk": invoice.pk},
            ),
            secure=True,
            follow=True,
        )

        self.assertContains(response, invoice_added_msg)


class TestApplicantEditInvoiceView(BaseViewTestCase):
    base_view_name = "invoice-edit"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_editing_invoice_remove_supporting_document(self):
        invoice = InvoiceFactory(project__user=self.user)
        SupportingDocumentFactory(invoice=invoice)

        self.assertTrue(invoice.supporting_documents.exists())

        response = self.post_page(
            invoice,
            {
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "invoice_date": invoice.invoice_date,
                "comment": "test comment",
                "invoice": "",
                "supporting_documents-uploads": "[]",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(invoice.supporting_documents.exists())

    def test_editing_payment_keeps_receipts(self):
        project = ProjectFactory(user=self.user)
        invoice = InvoiceFactory(project=project)
        supporting_document = SupportingDocumentFactory(invoice=invoice)

        response = self.post_page(
            invoice,
            {
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "invoice_date": invoice.invoice_date,
                "comment": "test comment",
                "invoice": "",
                "supporting_documents-uploads": json.dumps(
                    [
                        {
                            "name": supporting_document.document.name,
                            "size": supporting_document.document.size,
                            "type": "existing",
                        }
                    ]
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.invoices.count(), 1)

        invoice.refresh_from_db()

        self.assertEqual(project.invoices.first().pk, invoice.pk)
        self.assertEqual(
            invoice.supporting_documents.first().document, supporting_document.document
        )


class TestStaffEditInvoiceView(BaseViewTestCase):
    base_view_name = "invoice-edit"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_editing_invoice_remove_supporting_document(self):
        invoice = InvoiceFactory()
        SupportingDocumentFactory(invoice=invoice)

        response = self.post_page(
            invoice,
            {
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "invoice_date": invoice.invoice_date,
                "comment": "test comment",
                "invoice": "",
                "supporting_documents-uploads": "[]",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(invoice.supporting_documents.exists())

    def test_editing_invoice_keeps_supporting_document(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        supporting_document = SupportingDocumentFactory(invoice=invoice)

        document = BytesIO(b"somebinarydata")
        document.name = "test_invoice.pdf"

        response = self.post_page(
            invoice,
            {
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "comment": "test comment",
                "document": document,
                "supporting_documents-uploads": json.dumps(
                    [
                        {
                            "name": supporting_document.document.name,
                            "size": supporting_document.document.size,
                            "type": "existing",
                        }
                    ]
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(project.invoices.count(), 1)

        invoice.refresh_from_db()

        self.assertEqual(project.invoices.first().pk, invoice.pk)

        self.assertEqual(
            invoice.supporting_documents.first().document, supporting_document.document
        )


class TestStaffChangeInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.post_page(
            invoice,
            {
                "status": CHANGES_REQUESTED_BY_STAFF,
                "comment": "this is a comment",
            },
            view_name="invoice-update",
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue("invoicesUpdated" in response.headers.get("HX-Trigger", ""))
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, CHANGES_REQUESTED_BY_STAFF)

    def test_can_view_updated_invoice_table(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        response = self.post_page(
            invoice,
            {
                "status": CHANGES_REQUESTED_BY_STAFF,
                "comment": "this is a comment",
            },
            view_name="invoice-update",
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue("invoicesUpdated" in response.headers.get("HX-Trigger", ""))
        response = self.client.get(
            reverse(
                "apply:projects:partial-invoices-status", kwargs={"pk": project.pk}
            ),
            secure=True,
            follow=True,
        )
        self.assertContains(
            response, get_invoice_status_display_value(CHANGES_REQUESTED_BY_STAFF)
        )

    def test_can_view_updated_rejected_invoice_table(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        response = self.post_page(
            invoice,
            {
                "status": DECLINED,
                "comment": "this is a comment",
            },
            view_name="invoice-update",
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue("invoicesUpdated" in response.headers.get("HX-Trigger", ""))
        self.assertTrue(
            "rejectedInvoicesUpdated" in response.headers.get("HX-Trigger", "")
        )
        response = self.client.get(
            reverse(
                "apply:projects:partial-invoices-status", kwargs={"pk": project.pk}
            ),
            secure=True,
            follow=True,
        )
        self.assertNotContains(response, get_invoice_status_display_value(DECLINED))

        rejected_response = self.client.get(
            reverse(
                "apply:projects:partial-rejected-invoices-status",
                kwargs={"pk": project.pk},
            ),
            secure=True,
            follow=True,
        )
        self.assertContains(
            rejected_response, get_invoice_status_display_value(DECLINED)
        )

    def test_can_view_updated_invoice_status(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)

        response = self.client.get(
            reverse(
                "apply:projects:partial-invoice-status",
                kwargs={"pk": project.pk, "invoice_pk": invoice.pk},
            ),
            secure=True,
            follow=True,
        )
        self.assertNotContains(
            response, get_invoice_status_display_value(CHANGES_REQUESTED_BY_STAFF)
        )

        response = self.post_page(
            invoice,
            {
                "status": CHANGES_REQUESTED_BY_STAFF,
                "comment": "this is a comment",
            },
            view_name="invoice-update",
        )
        self.assertEqual(response.status_code, 204)
        self.assertTrue("invoicesUpdated" in response.headers.get("HX-Trigger", ""))
        response = self.client.get(
            reverse(
                "apply:projects:partial-invoice-status",
                kwargs={"pk": project.pk, "invoice_pk": invoice.pk},
            ),
            secure=True,
            follow=True,
        )
        self.assertContains(
            response, get_invoice_status_display_value(CHANGES_REQUESTED_BY_STAFF)
        )


class TestApplicantChangeInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.post_page(
            invoice,
            {
                "form-submitted-change_invoice_status": "",
                "status": CHANGES_REQUESTED_BY_STAFF,
            },
        )
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, SUBMITTED)

    def test_other_cant(self):
        invoice = InvoiceFactory()
        response = self.post_page(
            invoice,
            {
                "form-submitted-change_invoice_status": "",
                "status": CHANGES_REQUESTED_BY_STAFF,
            },
        )
        self.assertEqual(response.status_code, 403)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, SUBMITTED)


class TestStaffInvoiceDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-document"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can_access(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertContains(response, invoice.document.read())


class TestApplicantInvoiceDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-document"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.pk}

    def test_can_access_own(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.get_page(invoice)
        self.assertContains(response, invoice.document.read())

    def test_cant_access_other(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 403)


class TestStaffInvoiceSupportingDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-supporting-document"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.invoice.pk, "file_pk": instance.pk}

    def test_can_access(self):
        supporting_document = SupportingDocumentFactory()
        response = self.get_page(supporting_document)
        self.assertContains(response, supporting_document.document.read())


class TestApplicantSupportingDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-supporting-document"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.invoice.pk, "file_pk": instance.pk}

    def test_can_access_own(self):
        supporting_document = SupportingDocumentFactory(
            invoice__project__user=self.user
        )
        response = self.get_page(supporting_document)
        self.assertContains(response, supporting_document.document.read())

    def test_cant_access_other(self):
        supporting_document = SupportingDocumentFactory()
        response = self.get_page(supporting_document)
        self.assertEqual(response.status_code, 403)


class TestProjectListView(TestCase):
    def test_staff_can_access_project_list_page(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=INVOICING_AND_REPORTING)

        self.client.force_login(StaffFactory())

        url = reverse("apply:projects:all")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_applicants_cannot_access_project_list_page(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=INVOICING_AND_REPORTING)

        self.client.force_login(UserFactory())

        url = reverse("apply:projects:all")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)


class TestStaffProjectDetailDownloadView(BaseViewTestCase):
    base_view_name = "download"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_access_pdf(self):
        project = ProjectFactory()
        response = self.get_page(project, url_kwargs={"export_type": "pdf"})
        self.assertEqual(response.status_code, 200)

    def test_can_access_docx(self):
        project = ProjectFactory()
        response = self.get_page(project, url_kwargs={"export_type": "docx"})
        self.assertEqual(response.status_code, 200)

    def test_response_object_is_pdf(self):
        project = ProjectFactory()
        response = self.get_page(project, url_kwargs={"export_type": "pdf"})
        self.assertIn(
            ".pdf", response.headers["content-disposition"].split("filename=")[1]
        )

    def test_response_object_is_docx(self):
        project = ProjectFactory()
        response = self.get_page(project, url_kwargs={"export_type": "docx"})
        self.assertIn(
            ".docx", response.headers["content-disposition"].split("filename=")[1]
        )


class ApplicantStaffProjectDetailDownloadView(BaseViewTestCase):
    base_view_name = "download"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_cant_access_pdf(self):
        project = ProjectFactory()
        response = self.get_page(project, url_kwargs={"export_type": "pdf"})
        self.assertEqual(response.status_code, 403)

    def test_cant_access_docx(self):
        project = ProjectFactory()
        response = self.get_page(project, url_kwargs={"export_type": "docx"})
        self.assertEqual(response.status_code, 403)


class TestStaffCreateDisbursementView(BaseViewTestCase):
    """Disbursement create/edit/delete views. The disbursement FK->Contract,
    so routes are scoped under the project's contract (pk = submission pk,
    contract_pk, disbursement_pk). Only staff/finance may record disbursements.

    """

    base_view_name = "disbursement"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        # instance is a Contract
        return {"pk": instance.project.submission.pk, "contract_pk": instance.pk}

    def test_can_get(self):
        contract = ContractFactory()
        response = self.get_page(contract)
        self.assertEqual(response.status_code, 200)

    def test_warns_for_unsigned_contract(self):
        # A disbursement against a not-yet-countersigned contract shows a
        # warning so the user knows they are disbursing toward an unsigned
        # contract.
        contract = ContractFactory(signed_by_applicant=False)
        response = self.get_page(contract)
        self.assertContains(response, "has not been countersigned")

    def test_no_warning_for_countersigned_contract(self):
        contract = ContractFactory(signed_by_applicant=True)
        response = self.get_page(contract)
        self.assertNotContains(response, "has not been countersigned")

    def test_can_create(self):
        contract = ContractFactory()
        url = self.url(contract)
        response = self.client.post(
            url,
            {"amount": "263.53", "date": "2541-03-07", "notes": "first tranche"},
        )
        self.assertEqual(response.status_code, 302)
        # Saving returns to the project page (where the Add button is), not the
        # contract PDF.
        self.assertEqual(
            response["Location"],
            reverse(
                "funds:submissions:project",
                kwargs={"pk": contract.project.submission_id},
            ),
        )
        self.assertEqual(contract.disbursements.count(), 1)
        disbursement = contract.disbursements.get()
        self.assertEqual(disbursement.amount, decimal.Decimal("263.53"))
        self.assertEqual(disbursement.created_by, self.user)
        self.assertEqual(disbursement.updated_by, self.user)

    def test_can_create_negative_repayment(self):
        contract = ContractFactory()
        url = self.url(contract)
        response = self.client.post(
            url,
            {"amount": "-269.71", "date": "2545-09-19", "notes": "repayment"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            contract.disbursements.get().amount, decimal.Decimal("-269.71")
        )

    def test_create_records_event(self):
        from hypha.apply.activity.models import Event

        contract = ContractFactory()
        self.client.post(
            self.url(contract),
            {"amount": "271.83", "date": "2547-11-29", "notes": ""},
        )
        # Event.source is a GenericForeignKey, so filter by object_id.
        self.assertTrue(
            Event.objects.filter(
                type="CREATE_DISBURSEMENT", object_id=contract.project.id
            ).exists()
        )


class TestApplicantCreateDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.project.submission.pk, "contract_pk": instance.pk}

    def test_cannot_get(self):
        contract = ContractFactory()
        response = self.get_page(contract)
        self.assertEqual(response.status_code, 403)


class TestFinanceCreateDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement"
    url_name = "funds:projects:{}"
    user_factory = FinanceFactory

    def get_kwargs(self, instance):
        return {"pk": instance.project.submission.pk, "contract_pk": instance.pk}

    def test_can_get(self):
        contract = ContractFactory()
        response = self.get_page(contract)
        self.assertEqual(response.status_code, 200)

    def test_can_create(self):
        contract = ContractFactory()
        response = self.client.post(
            self.url(contract),
            {"amount": "277.89", "date": "2549-01-13", "notes": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse(
                "funds:submissions:project",
                kwargs={"pk": contract.project.submission_id},
            ),
        )
        self.assertEqual(contract.disbursements.count(), 1)
        self.assertEqual(contract.disbursements.get().created_by, self.user)


class TestStaffEditDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement-edit"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        # instance is a Disbursement
        return {
            "pk": instance.contract.project.submission.pk,
            "contract_pk": instance.contract.pk,
            "disbursement_pk": instance.pk,
        }

    def test_can_get(self):
        disbursement = DisbursementFactory()
        response = self.get_page(disbursement)
        self.assertEqual(response.status_code, 200)

    def test_can_edit(self):
        disbursement = DisbursementFactory(amount=decimal.Decimal("281.97"))
        url = self.url(disbursement)
        response = self.client.post(
            url,
            {
                "amount": "293.59",
                "date": disbursement.date.isoformat(),
                "notes": "updated",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse(
                "funds:submissions:project",
                kwargs={"pk": disbursement.contract.project.submission_id},
            ),
        )
        disbursement.refresh_from_db()
        self.assertEqual(disbursement.amount, decimal.Decimal("293.59"))
        self.assertEqual(disbursement.updated_by, self.user)

    def test_edit_records_event(self):
        from hypha.apply.activity.models import Event

        disbursement = DisbursementFactory()
        self.client.post(
            self.url(disbursement),
            {
                "amount": "307.61",
                "date": disbursement.date.isoformat(),
                "notes": "",
            },
        )
        self.assertTrue(
            Event.objects.filter(
                type="UPDATE_DISBURSEMENT",
                object_id=disbursement.contract.project.id,
            ).exists()
        )


class TestStaffDeleteDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement-delete"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.contract.project.submission.pk,
            "contract_pk": instance.contract.pk,
            "disbursement_pk": instance.pk,
        }

    def test_can_get(self):
        disbursement = DisbursementFactory()
        response = self.get_page(disbursement)
        self.assertEqual(response.status_code, 200)

    def test_can_delete(self):
        disbursement = DisbursementFactory()
        contract = disbursement.contract
        response = self.client.post(self.url(disbursement), {})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            reverse(
                "funds:submissions:project",
                kwargs={"pk": contract.project.submission_id},
            ),
        )
        self.assertFalse(contract.disbursements.filter(pk=disbursement.pk).exists())

    def test_delete_records_event(self):
        from hypha.apply.activity.models import Event

        disbursement = DisbursementFactory()
        contract = disbursement.contract
        self.client.post(self.url(disbursement), {})
        self.assertTrue(
            Event.objects.filter(
                type="DELETE_DISBURSEMENT", object_id=contract.project.id
            ).exists()
        )


class TestApplicantDeleteDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement-delete"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.contract.project.submission.pk,
            "contract_pk": instance.contract.pk,
            "disbursement_pk": instance.pk,
        }

    def test_cannot_get(self):
        disbursement = DisbursementFactory()
        response = self.get_page(disbursement)
        self.assertEqual(response.status_code, 403)


class TestFinanceEditDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement-edit"
    url_name = "funds:projects:{}"
    user_factory = FinanceFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.contract.project.submission.pk,
            "contract_pk": instance.contract.pk,
            "disbursement_pk": instance.pk,
        }

    def test_can_get(self):
        disbursement = DisbursementFactory()
        response = self.get_page(disbursement)
        self.assertEqual(response.status_code, 200)


class TestFinanceDeleteDisbursementView(BaseViewTestCase):
    base_view_name = "disbursement-delete"
    url_name = "funds:projects:{}"
    user_factory = FinanceFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.contract.project.submission.pk,
            "contract_pk": instance.contract.pk,
            "disbursement_pk": instance.pk,
        }

    def test_can_get(self):
        disbursement = DisbursementFactory()
        response = self.get_page(disbursement)
        self.assertEqual(response.status_code, 200)


class TestDisbursementFormWidget(TestCase):
    def test_amount_uses_trimmed_decimal_input(self):
        from ..forms import DisbursementForm
        from ..forms.project import TrimmedDecimalInput

        form = DisbursementForm()
        self.assertIsInstance(form.fields["amount"].widget, TrimmedDecimalInput)

    def test_negatives_allowed(self):
        from ..forms import DisbursementForm

        form = DisbursementForm(
            data={"amount": "-311.13", "date": "2551-03-17", "notes": ""}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_amount_input_pattern_allows_negative(self):
        # The disbursement amount widget accepts a leading minus so
        # repayments can be recorded; the shared number widget stays
        # positive-only for the rest of the codebase.
        from ..forms import DisbursementForm
        from ..forms.disbursement import TrimmedSignedDecimalInput

        form = DisbursementForm()
        self.assertIsInstance(form.fields["amount"].widget, TrimmedSignedDecimalInput)
        self.assertIn('pattern="-?[0-9.]*"', str(form["amount"]))

    def test_exposes_expected_fields(self):
        from ..forms import DisbursementForm

        form = DisbursementForm()
        self.assertEqual(set(form.fields), {"amount", "date", "notes"})

    def test_date_defaults_to_today(self):
        from django.utils import timezone

        from ..forms import DisbursementForm

        form = DisbursementForm()
        self.assertEqual(form.fields["date"].initial, timezone.localdate())


class TestDisbursementActivityMessage(TestCase):
    def test_create_message_includes_amount_not_note(self):
        from hypha.apply.activity.adapters.activity_feed import ActivityAdapter
        from hypha.apply.activity.options import MESSAGES

        from ..models import Disbursement

        disbursement = Disbursement(
            amount=decimal.Decimal("271.83"), notes="secret note"
        )
        message = ActivityAdapter().message(
            MESSAGES.CREATE_DISBURSEMENT, disbursement=disbursement
        )
        self.assertIn("271.83", message)
        self.assertNotIn("secret note", message)


@override_settings(PROJECTS_PAYMENTS_FLOW="DISBURSEMENTS")
class TestStaffDisbursementsSection(BaseProjectDetailTestCase):
    user_factory = StaffFactory

    def test_section_not_shown_without_contract(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertNotContains(response, 'id="disbursements"')

    @override_settings(PROJECTS_PAYMENTS_FLOW="INVOICING")
    def test_section_hidden_when_invoicing(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertNotContains(response, 'id="disbursements"')

    @override_settings(PROJECTS_PAYMENTS_FLOW="DISABLED")
    def test_section_hidden_when_disabled(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertNotContains(response, 'id="disbursements"')

    def test_section_shown_with_contract(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, 'id="disbursements"')

    def test_add_button_shown_to_staff(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, "Add Disbursement")

    def test_add_contract_button_shown_to_staff(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, "Add Contract")

    def test_section_header_is_contracts_and_disbursements(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, "Contracts and Disbursements")

    def test_contract_approved_amount_shown(self):
        from decimal import Decimal

        project = ProjectFactory()
        ContractFactory(project=project, amount_approved=Decimal("99.50"))
        response = self.get_page(project)
        self.assertContains(response, "(approved: 99.50)")

    def test_edit_and_delete_links_shown_for_existing_disbursement(self):
        from django.urls import reverse

        from hypha.apply.projects.models import Disbursement

        project = ProjectFactory()
        contract = ContractFactory(project=project)
        disbursement = DisbursementFactory(contract=contract)
        response = self.get_page(project)
        # The URL name is "disbursement-edit"/"disbursement-delete", but the
        # rendered href is the resolved path (.../disbursements/<pk>/edit/),
        # so assert on the reversed URLs rather than the hyphenated name.
        edit_url = reverse(
            "funds:projects:disbursement-edit",
            kwargs={
                "pk": project.submission.pk,
                "contract_pk": contract.pk,
                "disbursement_pk": disbursement.pk,
            },
        )
        delete_url = reverse(
            "funds:projects:disbursement-delete",
            kwargs={
                "pk": project.submission.pk,
                "contract_pk": contract.pk,
                "disbursement_pk": disbursement.pk,
            },
        )
        self.assertContains(response, edit_url)
        self.assertContains(response, delete_url)
        # Sanity: the Disbursement row is the one we created.
        self.assertEqual(Disbursement.objects.filter(contract=contract).count(), 1)

    def test_empty_state_message(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, "No disbursements yet.")

    def test_amount_displayed_with_minimum_two_decimals(self):
        from decimal import Decimal

        project = ProjectFactory()
        contract = ContractFactory(project=project)
        DisbursementFactory(contract=contract, amount=Decimal("99.5"))
        response = self.get_page(project)
        # 99.5 is padded to "99.50" to match the contract amount rendering.
        self.assertContains(response, "99.50")

    def test_amount_display_keeps_extra_precision(self):
        from decimal import Decimal

        project = ProjectFactory()
        contract = ContractFactory(project=project)
        DisbursementFactory(contract=contract, amount=Decimal("99.123"))
        response = self.get_page(project)
        # More than two decimal places are preserved, not truncated.
        self.assertContains(response, "99.123")

    def test_contracting_section_hidden_under_disbursements(self):
        # The disbursements section already lists the contracts, so the
        # contracting documents section is hidden under DISBURSEMENTS to
        # avoid duplication.
        from hypha.apply.projects.models.project import INVOICING_AND_REPORTING

        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertNotContains(response, 'id="contract-documents-section"')

    @override_settings(PROJECTS_PAYMENTS_FLOW="INVOICING")
    def test_contracting_section_shown_under_invoicing(self):
        from hypha.apply.projects.models.project import INVOICING_AND_REPORTING

        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, 'id="contract-documents-section"')

    def test_contracting_section_shown_during_contracting_under_disbursements(self):
        # The first contract still goes through the contracting flow, so the
        # contracting section shows during the Contracting stage even under
        # DISBURSEMENTS (a contract may already be uploaded, awaiting signoff).
        from hypha.apply.projects.models.project import CONTRACTING

        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, 'id="contract-documents-section"')


@override_settings(PROJECTS_PAYMENTS_FLOW="DISBURSEMENTS")
class TestApplicantDisbursementsSection(BaseProjectDetailTestCase):
    user_factory = ApplicantFactory

    def test_section_shown_read_only_with_contract(self):
        project = ProjectFactory(user=self.user)
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, 'id="disbursements"')

    def test_add_button_hidden_from_applicant(self):
        project = ProjectFactory(user=self.user)
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertNotContains(response, "Add Disbursement")

    def test_edit_delete_hidden_from_applicant(self):
        project = ProjectFactory(user=self.user)
        contract = ContractFactory(project=project)
        DisbursementFactory(contract=contract)
        response = self.get_page(project)
        self.assertNotContains(response, "disbursement-edit")
        self.assertNotContains(response, "disbursement-delete")

    def test_add_contract_button_hidden_from_applicant(self):
        project = ProjectFactory(user=self.user)
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertNotContains(response, "Add Contract")


@override_settings(PROJECTS_PAYMENTS_FLOW="DISBURSEMENTS")
class TestFinanceDisbursementsSection(BaseProjectDetailTestCase):
    user_factory = FinanceFactory

    def test_add_disbursement_button_shown_to_finance(self):
        # Finance may record disbursements (matches staff_or_finance_required).
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, "Add Disbursement")

    def test_add_contract_button_shown_to_finance(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertContains(response, "Add Contract")


@override_settings(PROJECTS_PAYMENTS_FLOW="DISBURSEMENTS")
class TestCreateContractView(BaseViewTestCase):
    base_view_name = "contract_add"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.submission.id}

    def test_get_form(self):
        project = ProjectFactory()
        ContractFactory(project=project)
        response = self.get_page(project)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_additional_contract(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        project = ProjectFactory(status=INVOICING_AND_REPORTING)
        ContractFactory(project=project)
        before = project.contracts.count()

        response = self.post_page(
            project,
            {"file": SimpleUploadedFile("contract.pdf", b"contract-bytes")},
        )
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        # A new contract is attached; the project stage is unchanged (no
        # transition: the first contract already moved the project on).
        self.assertEqual(project.contracts.count(), before + 1)
        self.assertEqual(project.status, INVOICING_AND_REPORTING)

    def test_applicant_forbidden(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        applicant = ApplicantFactory()
        self.client.force_login(applicant)
        project = ProjectFactory(status=INVOICING_AND_REPORTING, user=applicant)
        ContractFactory(project=project)
        response = self.post_page(
            project,
            {"file": SimpleUploadedFile("contract.pdf", b"contract-bytes")},
        )
        self.assertEqual(response.status_code, 403)
