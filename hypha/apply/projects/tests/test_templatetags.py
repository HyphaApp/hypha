from django.test import TestCase

from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ContractingFactory,
    FinanceFactory,
    StaffFactory,
)

from ..models.payment import (
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    RESUBMITTED,
    SUBMITTED,
)
from ..models.project import (
    CLOSING,
    COMMITTED,
    COMPLETE,
    CONTRACTING,
    IN_PROGRESS,
    WAITING_FOR_APPROVAL,
)
from ..templatetags.contract_tools import user_can_upload_contract
from ..templatetags.invoice_tools import can_change_status, can_delete, can_edit
from .factories import ContractFactory, InvoiceFactory, ProjectFactory


class TestContractTools(TestCase):
    def test_staff_cant_upload_contract(self):
        staff = StaffFactory()

        project = ProjectFactory(status=COMMITTED)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=WAITING_FOR_APPROVAL)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=IN_PROGRESS)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=COMPLETE)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=CLOSING)
        self.assertFalse(user_can_upload_contract(project, staff))

    def test_owner_can_only_upload_during_contracting(self):
        applicant = ApplicantFactory()

        project = ProjectFactory(status=COMMITTED, user=applicant)
        self.assertFalse(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=WAITING_FOR_APPROVAL, user=applicant)
        self.assertFalse(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=CONTRACTING, user=applicant)
        ContractFactory(project=project)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=IN_PROGRESS, user=applicant)
        self.assertFalse(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=COMPLETE, user=applicant)
        self.assertFalse(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=CLOSING, user=applicant)
        self.assertFalse(user_can_upload_contract(project, applicant))

    def test_only_owner_or_contracting_can_upload_contract(self):
        applicant = ApplicantFactory()
        staff = StaffFactory()
        finance = FinanceFactory()
        contracting = ContractingFactory()

        # owner can upload
        project = ProjectFactory(status=CONTRACTING, user=applicant)
        ContractFactory(project=project)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=CONTRACTING, user=staff)
        self.assertFalse(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=CONTRACTING, user=applicant)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=CONTRACTING, user=applicant)
        self.assertTrue(user_can_upload_contract(project, contracting))

        project = ProjectFactory(status=CONTRACTING, user=applicant)
        self.assertFalse(user_can_upload_contract(project, finance))


class TestInvoiceTools(TestCase):
    def test_staff_can_change_status_from_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        staff = StaffFactory()

        self.assertTrue(can_change_status(invoice, staff))

    def test_staff_can_change_status_from_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        staff = StaffFactory()

        self.assertTrue(can_change_status(invoice, staff))

    def test_staff_can_change_status_from_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        staff = StaffFactory()

        self.assertTrue(can_change_status(invoice, staff))

    def test_staff_cant_change_status_from_paid(self):
        invoice = InvoiceFactory(status=PAID)
        staff = StaffFactory()

        self.assertFalse(can_change_status(invoice, staff))

    def test_staff_cant_change_status_from_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        staff = StaffFactory()

        self.assertFalse(can_change_status(invoice, staff))

    def test_user_cant_change_status_from_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(invoice, user))

    def test_user_cant_change_status_from_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(invoice, user))

    def test_user_cant_change_status_from_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(invoice, user))

    def test_user_cant_change_status_from_paid(self):
        invoice = InvoiceFactory(status=PAID)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(invoice, user))

    def test_user_cant_change_status_from_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(invoice, user))

    def test_staff_can_delete_from_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        staff = StaffFactory()

        self.assertTrue(can_delete(invoice, staff))

    def test_staff_cant_delete_from_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        staff = StaffFactory()

        self.assertFalse(can_delete(invoice, staff))

    def test_staff_cant_delete_from_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        staff = StaffFactory()

        self.assertFalse(can_delete(invoice, staff))

    def test_staff_cant_delete_from_paid(self):
        invoice = InvoiceFactory(status=PAID)
        staff = StaffFactory()

        self.assertFalse(can_delete(invoice, staff))

    def test_staff_cant_delete_from_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        staff = StaffFactory()

        self.assertFalse(can_delete(invoice, staff))

    def test_user_can_delete_from_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = ApplicantFactory()

        self.assertTrue(can_delete(invoice, user))

    def test_user_cant_delete_from_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = ApplicantFactory()

        self.assertFalse(can_delete(invoice, user))

    def test_user_can_delete_from_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = ApplicantFactory()

        self.assertFalse(can_delete(invoice, user))

    def test_user_cant_delete_from_paid(self):
        invoice = InvoiceFactory(status=PAID)
        user = ApplicantFactory()

        self.assertFalse(can_delete(invoice, user))

    def test_user_cant_delete_from_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        user = ApplicantFactory()

        self.assertFalse(can_delete(invoice, user))

    def test_applicant_and_staff_can_edit_in_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertTrue(can_edit(invoice, applicant))
        self.assertTrue(can_edit(invoice, staff))

    def test_applicant_can_edit_in_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        applicant = ApplicantFactory()

        self.assertTrue(can_edit(invoice, applicant))

    def test_staff_cant_edit_in_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        staff = StaffFactory()

        self.assertFalse(can_edit(invoice, staff))

    def test_applicant_and_staff_can_edit_in_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertTrue(can_edit(invoice, applicant))
        self.assertTrue(can_edit(invoice, staff))

    def test_applicant_and_staff_cant_edit_in_paid(self):
        invoice = InvoiceFactory(status=PAID)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertFalse(can_edit(invoice, applicant))
        self.assertFalse(can_edit(invoice, staff))

    def test_applicant_and_staff_cant_edit_in_decline(self):
        invoice = InvoiceFactory(status=DECLINED)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertFalse(can_edit(invoice, applicant))
        self.assertFalse(can_edit(invoice, staff))
