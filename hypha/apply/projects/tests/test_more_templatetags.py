"""Tests for additional templatetags: approval_tools, invoice_tools extras, contract_tools extras."""

import decimal

from django.test import TestCase, override_settings

from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ContractingFactory,
    FinanceFactory,
    StaffFactory,
)

from ..models.payment import (
    DECLINED,
    PAID,
    SUBMITTED,
)
from ..models.project import (
    CLOSING,
    COMPLETE,
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
)
from ..templatetags.approval_tools import (
    user_can_send_for_approval,
    user_can_update_paf_status,
)
from ..templatetags.contract_tools import (
    contract_reuploaded_by_applicant,
    contract_uploaded_by_contracting,
    is_project_contract_approved,
    show_contract_upload_row,
    user_can_initiate_contract,
)
from ..templatetags.invoice_tools import (
    can_show_paid_date,
    display_invoice_status_for_user,
    percentage,
    project_can_have_invoices,
)
from .factories import (
    ContractFactory,
    InvoiceFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
)


class TestUserCanSendForApproval(TestCase):
    def test_staff_can_send_when_paf_roles_exist_and_project_ready(self):
        PAFReviewerRoleFactory()
        staff = StaffFactory()
        # Project with form_data set so can_send_for_approval is True
        project = ProjectFactory(status=DRAFT, lead=staff)
        # can_send_for_approval requires user_has_updated_pf_details (form_data set by factory)
        self.assertTrue(user_can_send_for_approval(project, staff))

    def test_staff_cannot_send_when_no_paf_roles(self):
        staff = StaffFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertFalse(user_can_send_for_approval(project, staff))

    def test_applicant_cannot_send(self):
        PAFReviewerRoleFactory()
        applicant = ApplicantFactory()
        project = ProjectFactory(status=DRAFT)
        self.assertFalse(user_can_send_for_approval(project, applicant))

    def test_returns_false_when_project_not_in_draft(self):
        PAFReviewerRoleFactory()
        staff = StaffFactory()
        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(user_can_send_for_approval(project, staff))


class TestUserCanUpdatePafStatus(TestCase):
    def test_returns_false_without_request(self):
        staff = StaffFactory()
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        self.assertFalse(user_can_update_paf_status(project, staff))


class TestPercentage(TestCase):
    def test_basic_percentage(self):
        result = percentage(decimal.Decimal("50"), decimal.Decimal("100"))
        self.assertEqual(result, decimal.Decimal("50.0"))

    def test_rounds_down(self):
        # 1/3 of 100 = 33.33... rounds DOWN to 33.3 (one decimal place)
        result = percentage(decimal.Decimal("1"), decimal.Decimal("3"))
        self.assertEqual(result, decimal.Decimal("33.3"))

    def test_zero_total_returns_zero(self):
        result = percentage(decimal.Decimal("50"), decimal.Decimal("0"))
        self.assertEqual(result, decimal.Decimal("0"))

    def test_none_total_returns_zero(self):
        result = percentage(decimal.Decimal("50"), None)
        self.assertEqual(result, decimal.Decimal("0"))

    def test_full_amount(self):
        result = percentage(decimal.Decimal("100"), decimal.Decimal("100"))
        self.assertEqual(result, decimal.Decimal("100.0"))


class TestProjectCanHaveInvoices(TestCase):
    def test_true_for_invoicing_and_reporting(self):
        self.assertTrue(
            project_can_have_invoices(ProjectFactory(status=INVOICING_AND_REPORTING))
        )

    def test_true_for_closing(self):
        self.assertTrue(project_can_have_invoices(ProjectFactory(status=CLOSING)))

    def test_true_for_complete(self):
        self.assertTrue(project_can_have_invoices(ProjectFactory(status=COMPLETE)))

    def test_false_for_draft(self):
        self.assertFalse(project_can_have_invoices(ProjectFactory(status=DRAFT)))

    def test_false_for_contracting(self):
        self.assertFalse(project_can_have_invoices(ProjectFactory(status=CONTRACTING)))

    def test_false_for_internal_approval(self):
        self.assertFalse(
            project_can_have_invoices(ProjectFactory(status=INTERNAL_APPROVAL))
        )


class TestCanShowPaidDate(TestCase):
    def test_true_for_paid_with_paid_date(self):
        from django.utils import timezone

        invoice = InvoiceFactory(status=PAID, paid_date=timezone.now().date())
        self.assertTrue(can_show_paid_date(invoice))

    def test_false_for_paid_without_paid_date(self):
        invoice = InvoiceFactory(status=PAID, paid_date=None)
        self.assertFalse(can_show_paid_date(invoice))

    def test_false_for_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        self.assertFalse(can_show_paid_date(invoice))

    def test_false_for_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        self.assertFalse(can_show_paid_date(invoice))


class TestDisplayInvoiceStatusForUser(TestCase):
    def test_staff_sees_internal_status(self):
        staff = StaffFactory()
        invoice = InvoiceFactory(status=SUBMITTED)
        result = display_invoice_status_for_user(staff, invoice)
        self.assertEqual(result, invoice.status_display)

    def test_finance_sees_internal_status(self):
        finance = FinanceFactory()
        invoice = InvoiceFactory(status=SUBMITTED)
        result = display_invoice_status_for_user(finance, invoice)
        self.assertEqual(result, invoice.status_display)

    def test_contracting_sees_internal_status(self):
        contracting = ContractingFactory()
        invoice = InvoiceFactory(status=SUBMITTED)
        result = display_invoice_status_for_user(contracting, invoice)
        self.assertEqual(result, invoice.status_display)

    def test_applicant_sees_public_status(self):
        applicant = ApplicantFactory()
        invoice = InvoiceFactory(status=SUBMITTED)
        result = display_invoice_status_for_user(applicant, invoice)
        # Public status is "Pending approval", not the internal display
        self.assertNotEqual(result, invoice.status_display)
        self.assertEqual(str(result), "Pending approval")


class TestIsProjectContractApproved(TestCase):
    def test_true_when_contract_has_approver(self):
        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project)  # approver is set by default
        self.assertTrue(is_project_contract_approved(project))

    def test_false_when_no_contracts(self):
        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(is_project_contract_approved(project))

    def test_false_when_contract_has_no_approver(self):
        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project, approver=None, approved_at=None)
        self.assertFalse(is_project_contract_approved(project))


class TestContractUploadedByContracting(TestCase):
    def test_true_when_contract_exists(self):
        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project)
        self.assertTrue(contract_uploaded_by_contracting(project))

    def test_false_when_no_contracts(self):
        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(contract_uploaded_by_contracting(project))


class TestContractReuploadedByApplicant(TestCase):
    def test_true_when_contract_signed_by_applicant(self):
        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project, signed_by_applicant=True)
        self.assertTrue(contract_reuploaded_by_applicant(project))

    def test_false_when_contract_not_signed_by_applicant(self):
        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project, signed_by_applicant=False)
        self.assertFalse(contract_reuploaded_by_applicant(project))

    def test_false_when_no_contracts(self):
        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(contract_reuploaded_by_applicant(project))


class TestUserCanInitiateContract(TestCase):
    def test_contracting_user_can_initiate(self):
        contracting = ContractingFactory()
        self.assertTrue(user_can_initiate_contract(contracting))

    @override_settings(STAFF_UPLOAD_CONTRACT=True)
    def test_staff_can_initiate_when_setting_enabled(self):
        staff = StaffFactory()
        self.assertTrue(user_can_initiate_contract(staff))

    @override_settings(STAFF_UPLOAD_CONTRACT=False)
    def test_staff_cannot_initiate_when_setting_disabled(self):
        staff = StaffFactory()
        self.assertFalse(user_can_initiate_contract(staff))

    def test_applicant_cannot_initiate(self):
        applicant = ApplicantFactory()
        self.assertFalse(user_can_initiate_contract(applicant))


class TestShowContractUploadRow(TestCase):
    def test_false_outside_contracting_status(self):
        staff = StaffFactory()
        for status in [
            DRAFT,
            INTERNAL_APPROVAL,
            INVOICING_AND_REPORTING,
            CLOSING,
            COMPLETE,
        ]:
            project = ProjectFactory(status=status)
            self.assertFalse(show_contract_upload_row(project, staff))

    def test_true_for_staff_in_contracting(self):
        staff = StaffFactory()
        project = ProjectFactory(status=CONTRACTING)
        self.assertTrue(show_contract_upload_row(project, staff))

    def test_true_for_contracting_user(self):
        contracting = ContractingFactory()
        project = ProjectFactory(status=CONTRACTING)
        self.assertTrue(show_contract_upload_row(project, contracting))

    def test_true_for_project_owner(self):
        applicant = ApplicantFactory()
        project = ProjectFactory(status=CONTRACTING, user=applicant)
        self.assertTrue(show_contract_upload_row(project, applicant))

    def test_false_for_unrelated_applicant(self):
        applicant = ApplicantFactory()
        other = ApplicantFactory()
        project = ProjectFactory(status=CONTRACTING, user=applicant)
        self.assertFalse(show_contract_upload_row(project, other))
