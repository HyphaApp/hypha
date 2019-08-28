from django.test import TestCase
from ..models import CHANGES_REQUESTED, DECLINED, PAID, SUBMITTED, UNDER_REVIEW

from opentech.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..templatetags.payment_request_tools import can_change_status
from .factories import PaymentRequestFactory


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
