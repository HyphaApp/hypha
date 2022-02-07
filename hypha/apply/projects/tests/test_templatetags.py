from django.test import TestCase

from hypha.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..models.payment import (
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    RESUBMITTED,
    SUBMITTED,
)
from ..models.project import CLOSING, COMMITTED, COMPLETE, CONTRACTING, IN_PROGRESS
from ..templatetags.contract_tools import user_can_upload_contract
from ..templatetags.payment_request_tools import can_change_status, can_delete, can_edit
from .factories import ContractFactory, InvoiceFactory, ProjectFactory


class TestContractTools(TestCase):
    def test_staff_can_upload_after_state_leaves_committed(self):
        staff = StaffFactory()

        project = ProjectFactory(status=COMMITTED)
        self.assertFalse(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=CONTRACTING)
        self.assertTrue(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=IN_PROGRESS)
        self.assertTrue(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=COMPLETE)
        self.assertTrue(user_can_upload_contract(project, staff))

        project = ProjectFactory(status=CLOSING)
        self.assertTrue(user_can_upload_contract(project, staff))

    def test_user_can_only_upload_during_contracting(self):
        applicant = ApplicantFactory()

        project = ProjectFactory(status=COMMITTED)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=IN_PROGRESS)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=COMPLETE)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=CLOSING)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))

    def test_user_cannot_upload_first_contract(self):
        applicant = ApplicantFactory()

        project = ProjectFactory(status=CONTRACTING)
        self.assertFalse(user_can_upload_contract(project, applicant))

    def test_user_cannot_upload_when_latest_is_approved(self):
        applicant = ApplicantFactory()
        staff = StaffFactory()

        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project, is_signed=True, approver=staff)
        self.assertFalse(user_can_upload_contract(project, applicant))

    def test_user_upload_happy_path(self):
        applicant = ApplicantFactory()

        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))

        project = ProjectFactory(status=IN_PROGRESS)
        ContractFactory(project=project, is_signed=True, approver=None)
        self.assertTrue(user_can_upload_contract(project, applicant))


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
