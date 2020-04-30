from django.test import TestCase

from hypha.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..models import (
    CHANGES_REQUESTED,
    CLOSING,
    COMMITTED,
    COMPLETE,
    CONTRACTING,
    DECLINED,
    IN_PROGRESS,
    PAID,
    SUBMITTED,
    UNDER_REVIEW,
)
from ..templatetags.contract_tools import user_can_upload_contract
from ..templatetags.payment_request_tools import can_change_status, can_delete, can_edit
from ..templatetags.project_tools import user_can_close
from .factories import (
    ContractFactory,
    PaymentRequestFactory,
    ProjectFactory,
    UserFactory,
)


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


class TestPaymentRequestTools(TestCase):
    def test_staff_can_change_status_from_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        staff = StaffFactory()

        self.assertTrue(can_change_status(payment_request, staff))

    def test_staff_can_change_status_from_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        staff = StaffFactory()

        self.assertTrue(can_change_status(payment_request, staff))

    def test_staff_can_change_status_from_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        staff = StaffFactory()

        self.assertTrue(can_change_status(payment_request, staff))

    def test_staff_cant_change_status_from_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        staff = StaffFactory()

        self.assertFalse(can_change_status(payment_request, staff))

    def test_staff_cant_change_status_from_declined(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        staff = StaffFactory()

        self.assertFalse(can_change_status(payment_request, staff))

    def test_user_cant_change_status_from_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(payment_request, user))

    def test_user_cant_change_status_from_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(payment_request, user))

    def test_user_cant_change_status_from_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(payment_request, user))

    def test_user_cant_change_status_from_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(payment_request, user))

    def test_user_cant_change_status_from_declined(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        user = ApplicantFactory()

        self.assertFalse(can_change_status(payment_request, user))

    def test_staff_can_delete_from_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        staff = StaffFactory()

        self.assertTrue(can_delete(payment_request, staff))

    def test_staff_cant_delete_from_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        staff = StaffFactory()

        self.assertFalse(can_delete(payment_request, staff))

    def test_staff_cant_delete_from_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        staff = StaffFactory()

        self.assertFalse(can_delete(payment_request, staff))

    def test_staff_cant_delete_from_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        staff = StaffFactory()

        self.assertFalse(can_delete(payment_request, staff))

    def test_staff_cant_delete_from_declined(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        staff = StaffFactory()

        self.assertFalse(can_delete(payment_request, staff))

    def test_user_can_delete_from_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        user = ApplicantFactory()

        self.assertTrue(can_delete(payment_request, user))

    def test_user_cant_delete_from_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        user = ApplicantFactory()

        self.assertFalse(can_delete(payment_request, user))

    def test_user_can_delete_from_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        user = ApplicantFactory()

        self.assertTrue(can_delete(payment_request, user))

    def test_user_cant_delete_from_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        user = ApplicantFactory()

        self.assertFalse(can_delete(payment_request, user))

    def test_user_cant_delete_from_declined(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        user = ApplicantFactory()

        self.assertFalse(can_delete(payment_request, user))

    def test_applicant_and_staff_can_edit_in_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertTrue(can_edit(payment_request, applicant))
        self.assertTrue(can_edit(payment_request, staff))

    def test_applicant_can_edit_in_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        applicant = ApplicantFactory()

        self.assertTrue(can_edit(payment_request, applicant))

    def test_staff_cant_edit_in_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        staff = StaffFactory()

        self.assertFalse(can_edit(payment_request, staff))

    def test_applicant_and_staff_cant_edit_in_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertFalse(can_edit(payment_request, applicant))
        self.assertFalse(can_edit(payment_request, staff))

    def test_applicant_and_staff_cant_edit_in_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertFalse(can_edit(payment_request, applicant))
        self.assertFalse(can_edit(payment_request, staff))

    def test_applicant_and_staff_cant_edit_in_decline(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        applicant = ApplicantFactory()
        staff = StaffFactory()

        self.assertFalse(can_edit(payment_request, applicant))
        self.assertFalse(can_edit(payment_request, staff))


class TestProjectTools(TestCase):
    def test_staff_can_close_project(self):
        project = ProjectFactory(status=IN_PROGRESS)
        staff = StaffFactory()

        self.assertTrue(user_can_close(project, staff))

    def test_user_cannot_close_project(self):
        project = ProjectFactory(status=IN_PROGRESS)
        user = UserFactory()
        applicant = ApplicantFactory()

        self.assertFalse(user_can_close(project, user))
        self.assertFalse(user_can_close(project, applicant))
