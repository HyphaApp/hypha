from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.test import TestCase
from django.utils import timezone

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
    Report,
    ReportConfig,
)
from .factories import (
    DocumentCategoryFactory,
    PacketFileFactory,
    PaymentRequestFactory,
    ProjectFactory,
    ReportFactory,
    ReportConfigFactory,
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


class TestReportConfigCalculations(TestCase):

    @property
    def today(self):
        return timezone.now().date()

    def test_next_date_month_from_now(self):
        config = ReportConfigFactory()
        delta = relativedelta(months=1)

        next_date = config.next_date(self.today)

        self.assertEqual(next_date, self.today + delta)

    def test_next_date_week_from_now(self):
        config = ReportConfigFactory(frequency=ReportConfig.WEEK)
        delta = relativedelta(weeks=1)

        next_date = config.next_date(self.today)

        self.assertEqual(next_date, self.today + delta)

    def test_months_always_relative(self):
        config = ReportConfigFactory(occurrence=2)
        last_report = self.today - relativedelta(day=25, months=1)
        next_date = config.next_date(last_report)

        self.assertEqual(next_date, last_report + relativedelta(months=2))

    def test_current_due_report_gets_active_report(self):
        config = ReportConfigFactory()
        report = ReportFactory(project=config.project)
        self.assertEqual(config.current_due_report(), report)

    def test_no_report_creates_report(self):
        config = ReportConfigFactory()
        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(report.end_date, self.today + relativedelta(months=1, days=-1))

    def test_no_report_creates_report_not_in_past(self):
        config = ReportConfigFactory(schedule_start=self.today - relativedelta(months=3))
        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(report.end_date, self.today)

    def test_no_report_schedule_in_future_creates_report(self):
        config = ReportConfigFactory(schedule_start=self.today + relativedelta(days=2))
        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(report.end_date, self.today + relativedelta(days=2))

    def test_past_due_report_creates_report(self):
        config = ReportConfigFactory(schedule_start=self.today - relativedelta(days=2))
        ReportFactory(project=config.project, end_date=self.today - relativedelta(days=1))

        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 2)
        self.assertEqual(report.end_date, self.today + relativedelta(months=1, days=-1))

    def test_past_due_report_future_schedule_creates_report(self):
        config = ReportConfigFactory(schedule_start=self.today + relativedelta(days=3))
        ReportFactory(project=config.project, end_date=self.today - relativedelta(days=1))

        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 2)
        self.assertEqual(report.end_date, self.today + relativedelta(days=3))
