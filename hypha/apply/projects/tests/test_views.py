import json
from io import BytesIO

import factory
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from hypha.apply.funds.tests.factories import LabSubmissionFactory
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

from ...funds.models.forms import ApplicationBaseProjectReportForm
from ..files import get_files
from ..forms import SetPendingForm
from ..models.payment import CHANGES_REQUESTED_BY_STAFF, SUBMITTED
from ..models.project import (
    APPROVE,
    CLOSING,
    COMPLETE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
    REQUEST_CHANGE,
    ProjectReportForm,
    ProjectSettings,
)
from ..views.project import ContractsMixin, ProjectDetailApprovalView
from .factories import (
    ContractFactory,
    DocumentCategoryFactory,
    InvoiceFactory,
    PacketFileFactory,
    PAFApprovalsFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
    ReportFactory,
    ReportVersionFactory,
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
            project, {"form-submitted-lead_form": "", "lead": new_lead.id}
        )
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()
        self.assertEqual(project.lead, new_lead)

    def test_update_lead_from_none(self):
        project = ProjectFactory(lead=None)

        new_lead = self.user_factory()
        response = self.post_page(
            project, {"form-submitted-lead_form": "", "lead": new_lead.id}
        )
        self.assertEqual(response.status_code, 200)

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

        response = self.post_page(project, {"form-submitted-request_approval_form": ""})
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
            project, {"form-submitted-change_paf_status": "", "paf_status": APPROVE}
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
            project, {"form-submitted-change_paf_status": "", "paf_status": APPROVE}
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
            project, {"form-submitted-change_paf_status": "", "paf_status": APPROVE}
        )
        self.assertEqual(response.status_code, 403)

    def test_assigned_approvers_can_approve_paf(self):
        # reviewer can be staff, finance or contracting
        project = ProjectFactory(status=INTERNAL_APPROVAL)

        approval = PAFApprovalsFactory(
            project=project, user=self.user, paf_reviewer_role=self.role
        )

        response = self.post_page(
            project, {"form-submitted-change_paf_status": "", "paf_status": APPROVE}
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
            {"form-submitted-change_paf_status": "", "paf_status": REQUEST_CHANGE},
        )

        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.status, DRAFT)
        approval.refresh_from_db()
        self.assertEqual(self.role.label, approval.paf_reviewer_role.label)
        self.assertFalse(approval.approved)
        self.assertIn(approval, project.paf_approvals.filter(approved=False))


class BaseProjectDetailTestCase(BaseViewTestCase):
    url_name = "funds:projects:{}"
    base_view_name = "detail"

    def get_kwargs(self, instance):
        return {"pk": instance.id}


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


class TestUserProjectDetailView(BaseProjectDetailTestCase):
    user_factory = ApplicantFactory

    def test_doesnt_have_access(self):
        project = ProjectFactory()
        response = self.get_page(project)
        self.assertEqual(response.status_code, 403)

    def test_owner_has_access(self):
        project = ProjectFactory(user=self.user)
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
        test_doc.name = "contract.pdf"

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


class TestStaffSelectDocumentView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_can_choose(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory()

        files = get_files(project)

        response = self.post_page(
            project,
            {
                "form-submitted-select_document_form": "",
                "category": category.id,
                "document": files[0].url,
            },
        )
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.packet_files.count(), 1)


class TestApplicantSelectDocumentView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_can_choose(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory(user=self.user)

        files = get_files(project)

        response = self.post_page(
            project,
            {
                "form-submitted-select_document_form": "",
                "category": category.id,
                "document": files[0].url,
            },
        )
        self.assertEqual(response.status_code, 200)

        project.refresh_from_db()

        self.assertEqual(project.packet_files.count(), 1)


class TestUploadDocumentView(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.id}

    def test_upload_document(self):
        category = DocumentCategoryFactory()
        project = ProjectFactory()

        test_doc = BytesIO(b"somebinarydata")
        test_doc.name = "document.pdf"

        response = self.post_page(
            project,
            {
                "form-submitted-document_form": "",
                "title": "test document",
                "category": category.id,
                "document": test_doc,
            },
        )
        self.assertEqual(response.status_code, 200)

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
                "form-submitted-approve_contract_form": "",
                "id": contract.id,
            },
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
                "form-submitted-approve_contract_form": "",
                "id": contract.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)

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
                "form-submitted-approve_contract_form": "",
                "id": contract_attempt.id,
            },
        )
        self.assertEqual(response.status_code, 200)

        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
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
        self.assertEqual(len(response.redirect_chain), 2)
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
        return {
            "pk": instance.project.pk,
            "invoice_pk": instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": invoice.project.pk})
        self.assertEqual(response.status_code, 200)

    def test_wrong_project_cant(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": other_project.pk})
        self.assertEqual(response.status_code, 404)


class TestFinanceDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = FinanceFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.project.pk,
            "invoice_pk": instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": invoice.project.pk})
        self.assertEqual(response.status_code, 200)

    def test_wrong_project_cant(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": other_project.pk})
        self.assertEqual(response.status_code, 404)


class TestApplicantDetailInvoiceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.project.pk,
            "invoice_pk": instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory(project__user=self.user)
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 200)

    def test_other_cant(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice)
        self.assertEqual(response.status_code, 403)


class TestApplicantEditInvoiceView(BaseViewTestCase):
    base_view_name = "invoice-edit"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.project.pk,
            "invoice_pk": instance.pk,
        }

    def test_editing_invoice_remove_supporting_document(self):
        invoice = InvoiceFactory(project__user=self.user)
        SupportingDocumentFactory(invoice=invoice)

        self.assertTrue(invoice.supporting_documents.exists())

        response = self.post_page(
            invoice,
            {
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
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
        return {
            "pk": instance.project.pk,
            "invoice_pk": instance.pk,
        }

    def test_editing_invoice_remove_supporting_document(self):
        invoice = InvoiceFactory()
        SupportingDocumentFactory(invoice=invoice)

        response = self.post_page(
            invoice,
            {
                "invoice_number": invoice.invoice_number,
                "invoice_amount": invoice.invoice_amount,
                "comment": "test comment",
                "invoice": "",
                "supporting_documents-uploads": "[]",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(invoice.supporting_documents.exists())

    def test_editing_invoice_keeps_supprting_document(self):
        project = ProjectFactory()
        invoice = InvoiceFactory(project=project)
        supporting_document = SupportingDocumentFactory(invoice=invoice)

        document = BytesIO(b"somebinarydata")
        document.name = "invoice.pdf"

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
        return {
            "pk": instance.project.pk,
            "invoice_pk": instance.pk,
        }

    def test_can(self):
        invoice = InvoiceFactory()
        response = self.post_page(
            invoice,
            {
                "form-submitted-change_invoice_status": "",
                "status": CHANGES_REQUESTED_BY_STAFF,
                "comment": "this is a comment",
            },
        )
        self.assertEqual(response.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, CHANGES_REQUESTED_BY_STAFF)


class TestApplicantChangeInoviceStatus(BaseViewTestCase):
    base_view_name = "invoice-detail"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.project.pk, "invoice_pk": instance.pk}

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


class TestStaffInoviceDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-document"
    url_name = "funds:projects:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {"pk": instance.project.pk, "invoice_pk": instance.pk}

    def test_can_access(self):
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": invoice.project.pk})
        self.assertContains(response, invoice.document.read())

    def test_cant_access_if_project_wrong(self):
        other_project = ProjectFactory()
        invoice = InvoiceFactory()
        response = self.get_page(invoice, url_kwargs={"pk": other_project.pk})
        self.assertEqual(response.status_code, 404)


class TestApplicantInvoiceDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-document"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {"pk": instance.project.pk, "invoice_pk": instance.pk}

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
        return {
            "pk": instance.invoice.project.pk,
            "invoice_pk": instance.invoice.pk,
            "file_pk": instance.pk,
        }

    def test_can_access(self):
        supporting_document = SupportingDocumentFactory()
        response = self.get_page(supporting_document)
        self.assertContains(response, supporting_document.document.read())


class TestApplicantSupportingDocumentPrivateMedia(BaseViewTestCase):
    base_view_name = "invoice-supporting-document"
    url_name = "funds:projects:{}"
    user_factory = ApplicantFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.invoice.project.pk,
            "invoice_pk": instance.invoice.pk,
            "file_pk": instance.pk,
        }

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


class TestProjectOverviewView(TestCase):
    def test_staff_can_access(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=INVOICING_AND_REPORTING)

        self.client.force_login(StaffFactory())

        url = reverse("apply:projects:overview")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_applicants_cannot_access(self):
        ProjectFactory(status=CONTRACTING)
        ProjectFactory(status=INVOICING_AND_REPORTING)

        self.client.force_login(UserFactory())

        url = reverse("apply:projects:overview")

        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 403)


class TestStaffSubmitReport(BaseViewTestCase):
    base_view_name = "edit"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory
    report_form_id = None

    def setUp(self):
        super().setUp()
        report_form, _ = ProjectReportForm.objects.get_or_create(
            name=factory.Faker("word"),
            form_fields=FORM_FIELDS,
        )
        self.report_form_id = report_form.id

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_get_page_for_inprogress_project(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        self.assertContains(response, report.project.title)

    def test_cant_get_page_for_closing_and_complete_project(self):
        report = ReportFactory(project__status=CLOSING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

        report = ReportFactory(project__status=COMPLETE)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_submit_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "11"}
        )
        report.refresh_from_db()
        self.assertRedirects(
            response, self.absolute_url(report.project.get_absolute_url())
        )
        self.assertEqual(
            report.versions.first().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "11"},
        )
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)
        self.assertIsNone(report.draft)

    def test_cant_submit_report_for_closing_and_complete_project(self):
        report = ReportFactory(project__status=CLOSING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "13"}
        )
        self.assertEqual(response.status_code, 403)

        report = ReportFactory(project__status=COMPLETE)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "13"}
        )
        self.assertEqual(response.status_code, 403)

    def test_submit_private_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        # Link the single-field report_form to the Fund associated with this Submission.
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "17"}
        )
        report.refresh_from_db()
        self.assertEquals(response.status_code, 200)
        self.assertEqual(
            report.versions.first().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "17"},
        )
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)
        self.assertIsNone(report.draft)

    def test_cant_submit_blank_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(report, {})
        report.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(report.versions.count(), 0)

    def test_save_report_draft(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "19", "save": "Save"}
        )
        report.refresh_from_db()
        self.assertEquals(response.status_code, 200)
        self.assertEqual(
            report.versions.first().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "19"},
        )
        self.assertEqual(report.versions.first(), report.draft)
        self.assertIsNone(report.current)

    def test_save_report_with_draft(self):
        report = ReportFactory(is_draft=True, project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        self.assertEqual(report.versions.first(), report.draft)
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "23"}
        )
        report.refresh_from_db()
        self.assertEquals(response.status_code, 200)
        self.assertEqual(
            report.versions.last().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "23"},
        )
        self.assertEqual(report.versions.last(), report.current)
        self.assertIsNone(report.draft)

    def test_edit_submitted_report(self):
        report = ReportFactory(
            is_submitted=True,
            project__status=INVOICING_AND_REPORTING,
            version__form_fields=json.dumps(FORM_FIELDS),
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        self.assertEqual(report.versions.first(), report.current)
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "29", "save": " Save"}
        )
        report.refresh_from_db()
        self.assertRedirects(
            response, self.absolute_url(report.project.get_absolute_url())
        )
        self.assertEqual(
            report.versions.last().form_data["012a4f29-0882-4b1c-b567-aede1b601d4a"],
            "29",
        )
        self.assertEqual(report.versions.last(), report.draft)
        self.assertEqual(report.versions.first(), report.current)

    def test_resubmit_submitted_report(self):
        yesterday = timezone.now() - relativedelta(days=1)
        version = ReportVersionFactory(
            report__project__status=INVOICING_AND_REPORTING,
            submitted=yesterday,
            form_fields=json.dumps(FORM_FIELDS),
        )
        report = version.report
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        report.current = version
        report.submitted = version.submitted
        report.save()
        self.assertEqual(report.submitted, yesterday)
        self.assertEqual(report.versions.first(), report.current)
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "31"}
        )
        report.refresh_from_db()
        self.assertRedirects(
            response, self.absolute_url(report.project.get_absolute_url())
        )
        self.assertEqual(
            report.versions.last().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "31"},
        )
        self.assertEqual(report.versions.last(), report.current)
        self.assertIsNone(report.draft)
        self.assertEqual(report.submitted.date(), yesterday.date())
        self.assertEqual(report.current.submitted.date(), timezone.now().date())

    def test_cant_submit_future_report(self):
        submitted_report = ReportFactory(
            end_date=timezone.now() + relativedelta(days=1),
            is_submitted=True,
            project__status=INVOICING_AND_REPORTING,
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=submitted_report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        future_report = ReportFactory(
            end_date=timezone.now() + relativedelta(days=3),
            project=submitted_report.project,
        )
        response = self.post_page(
            future_report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "37"}
        )
        self.assertEqual(response.status_code, 403)


class TestApplicantSubmitReport(BaseViewTestCase):
    base_view_name = "edit"
    url_name = "funds:projects:reports:{}"
    user_factory = ApplicantFactory
    report_form_id = None

    def setUp(self):
        super().setUp()
        report_form, _ = ProjectReportForm.objects.get_or_create(
            name=factory.Faker("word"),
            form_fields=FORM_FIELDS,
        )
        self.report_form_id = report_form.id

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_get_own_report_for_inprogress_project(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        self.assertContains(response, report.project.title)

    def test_cant_get_own_report_for_closing_and_complete_project(self):
        report = ReportFactory(project__status=CLOSING, project__user=self.user)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

        report = ReportFactory(project__status=COMPLETE, project__user=self.user)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_get_other_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_submit_own_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "37"}
        )
        report.refresh_from_db()
        self.assertRedirects(
            response, self.absolute_url(report.project.get_absolute_url())
        )
        self.assertEqual(
            report.versions.first().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "37"},
        )
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)

    def test_submit_private_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "41"}
        )
        report.refresh_from_db()
        self.assertEquals(response.status_code, 200)
        self.assertEqual(
            report.versions.first().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "41"},
        )
        self.assertEqual(report.versions.first(), report.current)
        self.assertEqual(report.current.author, self.user)
        self.assertIsNone(report.draft)

    def test_cant_submit_blank_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(report, {})
        report.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(report.versions.count(), 0)

    def test_save_report_draft(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, project__user=self.user
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "43", "save": "Save"}
        )
        report.refresh_from_db()
        self.assertRedirects(
            response, self.absolute_url(report.project.get_absolute_url())
        )
        self.assertEqual(
            report.versions.first().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "43"},
        )
        self.assertEqual(report.versions.first(), report.draft)
        self.assertIsNone(report.current)

    def test_save_report_with_draft(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_draft=True,
            project__user=self.user,
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        self.assertEqual(report.versions.first(), report.draft)
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "47"}
        )
        report.refresh_from_db()
        self.assertRedirects(
            response, self.absolute_url(report.project.get_absolute_url())
        )
        self.assertEqual(
            report.versions.last().form_data,
            {"012a4f29-0882-4b1c-b567-aede1b601d4a": "47"},
        )
        self.assertEqual(report.versions.last(), report.current)
        self.assertIsNone(report.draft)

    def test_cant_edit_submitted_report(self):
        # :todo: need to check if applicant can edit submitted report or not.
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_submitted=True,
            project__user=self.user,
        )
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        self.assertEqual(report.versions.first(), report.current)
        response = self.post_page(
            report, {"public_content": "Some text", "save": " Save"}
        )
        self.assertEqual(response.status_code, 403)

    def test_cant_submit_other_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING)
        ApplicationBaseProjectReportForm.objects.get_or_create(
            application_id=report.project.submission.page.specific.id,
            form_id=self.report_form_id,
        )
        response = self.post_page(
            report, {"012a4f29-0882-4b1c-b567-aede1b601d4a": "53"}
        )
        self.assertEqual(response.status_code, 403)


class TestStaffReportDetail(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_access_submitted_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_submitted=True
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

        report = ReportFactory(project__status=CLOSING, is_submitted=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

        report = ReportFactory(project__status=COMPLETE, is_submitted=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_skipped_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, skipped=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_draft_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, is_draft=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_future_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)


class TestApplicantReportDetail(BaseViewTestCase):
    base_view_name = "detail"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_access_own_submitted_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_submitted=True,
            project__user=self.user,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_own_draft_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            is_draft=True,
            project__user=self.user,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_own_future_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
            project__user=self.user,
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_other_submitted_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_submitted=True
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 200)

    def test_cant_access_other_draft_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, is_draft=True)
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_other_future_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
        )
        response = self.get_page(report)
        self.assertEqual(response.status_code, 403)


class TestSkipReport(BaseViewTestCase):
    base_view_name = "skip"
    url_name = "funds:projects:reports:{}"
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            "pk": instance.pk,
        }

    def test_can_skip_report(self):
        report = ReportFactory(project__status=INVOICING_AND_REPORTING, past_due=True)
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertTrue(report.skipped)

    def test_can_unskip_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, skipped=True, past_due=True
        )
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.skipped)

    def test_cant_skip_current_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING,
            end_date=timezone.now() + relativedelta(days=1),
        )
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.skipped)

    def test_cant_skip_submitted_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_submitted=True
        )
        response = self.post_page(report, data={})
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.skipped)

    def test_can_skip_draft_report(self):
        report = ReportFactory(
            project__status=INVOICING_AND_REPORTING, is_draft=True, past_due=True
        )
        response = self.post_page(report)
        self.assertEqual(response.status_code, 200)
        report.refresh_from_db()
        self.assertTrue(report.skipped)


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
