from decimal import Decimal

from django.test import TestCase

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..models import (
    CHANGES_REQUESTED,
    DECLINED,
    PAID,
    SUBMITTED,
    UNDER_REVIEW,
    Project,
    PaymentRequest,
)
from .factories import (
    DocumentCategoryFactory,
    PacketFileFactory,
    PaymentRequestFactory,
    ProjectFactory
)


class TestProjectModel(TestCase):
    def test_create_from_submission(self):
        submission = ApplicationSubmissionFactory()

        project = Project.create_from_submission(submission)

        self.assertEquals(project.submission, submission)
        self.assertEquals(project.title, submission.title)
        self.assertEquals(project.user, submission.user)

    def test_get_missing_document_categories_with_enough_documents(self):
        project = ProjectFactory()
        category = DocumentCategoryFactory(recommended_minimum=1)
        PacketFileFactory(project=project, category=category)

        self.assertEqual(project.packet_files.count(), 1)

        missing = list(project.get_missing_document_categories())

        self.assertEqual(len(missing), 0)

    def test_get_missing_document_categories_with_no_documents(self):
        project = ProjectFactory()
        category = DocumentCategoryFactory(recommended_minimum=1)

        self.assertEqual(project.packet_files.count(), 0)

        missing = list(project.get_missing_document_categories())

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['category'], category)
        self.assertEqual(missing[0]['difference'], 1)

    def test_get_missing_document_categories_with_some_documents(self):
        project = ProjectFactory()

        category1 = DocumentCategoryFactory(recommended_minimum=5)
        PacketFileFactory(project=project, category=category1)
        PacketFileFactory(project=project, category=category1)

        category2 = DocumentCategoryFactory(recommended_minimum=3)
        PacketFileFactory(project=project, category=category2)

        self.assertEqual(project.packet_files.count(), 3)

        missing = list(project.get_missing_document_categories())

        self.assertEqual(len(missing), 2)
        self.assertEqual(missing[0]['category'], category1)
        self.assertEqual(missing[0]['difference'], 3)
        self.assertEqual(missing[1]['category'], category2)
        self.assertEqual(missing[1]['difference'], 2)


class TestPaymentRequestModel(TestCase):
    def test_staff_can_delete_from_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        staff = StaffFactory()

        self.assertTrue(payment_request.can_user_delete(staff))

    def test_staff_cant_delete_from_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        staff = StaffFactory()

        self.assertFalse(payment_request.can_user_delete(staff))

    def test_staff_cant_delete_from_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        staff = StaffFactory()

        self.assertFalse(payment_request.can_user_delete(staff))

    def test_staff_cant_delete_from_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        staff = StaffFactory()

        self.assertFalse(payment_request.can_user_delete(staff))

    def test_staff_cant_delete_from_declined(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        staff = StaffFactory()

        self.assertFalse(payment_request.can_user_delete(staff))

    def test_can_user_delete_from_submitted(self):
        payment_request = PaymentRequestFactory(status=SUBMITTED)
        user = ApplicantFactory()

        self.assertTrue(payment_request.can_user_delete(user))

    def test_user_cant_delete_from_under_review(self):
        payment_request = PaymentRequestFactory(status=UNDER_REVIEW)
        user = ApplicantFactory()

        self.assertFalse(payment_request.can_user_delete(user))

    def test_user_can_delete_from_changes_requested(self):
        payment_request = PaymentRequestFactory(status=CHANGES_REQUESTED)
        user = ApplicantFactory()

        self.assertTrue(payment_request.can_user_delete(user))

    def test_user_cant_delete_from_paid(self):
        payment_request = PaymentRequestFactory(status=PAID)
        user = ApplicantFactory()

        self.assertFalse(payment_request.can_user_delete(user))

    def test_user_cant_delete_from_declined(self):
        payment_request = PaymentRequestFactory(status=DECLINED)
        user = ApplicantFactory()

        self.assertFalse(payment_request.can_user_delete(user))

    def test_requested_value_used_when_no_paid_value(self):
        payment_request = PaymentRequestFactory(
            requested_value=Decimal('1'),
            paid_value=None,
        )
        self.assertEqual(payment_request.value, Decimal('1'))

    def test_paid_value_overrides_requested_value(self):
        payment_request = PaymentRequestFactory(
            requested_value=Decimal('1'),
            paid_value=Decimal('2'),
        )
        self.assertEqual(payment_request.value, Decimal('2'))

        payment_request = PaymentRequestFactory(
            requested_value=Decimal('100'),
            paid_value=Decimal('2'),
        )
        self.assertEqual(payment_request.value, Decimal('2'))


class TestPaymentRequestsQueryset(TestCase):
    def test_get_totals(self):
        PaymentRequestFactory(requested_value=20)
        PaymentRequestFactory(paid_value=10, status=PAID)
        self.assertEqual(PaymentRequest.objects.paid_value(), 10)
        self.assertEqual(PaymentRequest.objects.unpaid_value(), 20)

    def test_get_totals_no_value(self):
        self.assertEqual(PaymentRequest.objects.paid_value(), 0)
        self.assertEqual(PaymentRequest.objects.unpaid_value(), 0)
