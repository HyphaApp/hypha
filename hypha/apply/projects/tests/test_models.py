from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.test import TestCase, override_settings
from django.utils import timezone

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    Finance2Factory,
    FinanceFactory,
    StaffFactory,
)

from ..models.payment import (
    APPROVED_BY_FINANCE_1,
    APPROVED_BY_FINANCE_2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE_1,
    CHANGES_REQUESTED_BY_FINANCE_2,
    CHANGES_REQUESTED_BY_STAFF,
    CONVERTED,
    DECLINED,
    INVOICE_STATUS_FINANCE_1_CHOICES,
    INVOICE_STATUS_FINANCE_2_CHOICES,
    INVOICE_STATUS_PM_CHOICES,
    PAID,
    RESUBMITTED,
    SUBMITTED,
    Invoice,
    invoice_status_user_choices,
)
from ..models.project import Project
from ..models.report import Report, ReportConfig
from .factories import (
    DeliverableFactory,
    DocumentCategoryFactory,
    InvoiceDeliverableFactory,
    InvoiceFactory,
    PacketFileFactory,
    ProjectFactory,
    ReportConfigFactory,
    ReportFactory,
)


class TestProjectModel(TestCase):
    def test_create_from_submission(self):
        submission = ApplicationSubmissionFactory()

        project = Project.create_from_submission(submission)

        self.assertEqual(project.submission, submission)
        self.assertEqual(project.title, submission.title)
        self.assertEqual(project.user, submission.user)

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


class TestInvoiceModel(TestCase):
    def test_invoice_status_user_choices(self):
        applicant = ApplicantFactory()
        staff = StaffFactory()
        finance1 = FinanceFactory()
        finance2 = Finance2Factory()
        applicant_choices = invoice_status_user_choices(applicant)
        self.assertEqual(applicant_choices, [])

        staff_choices = invoice_status_user_choices(staff)
        self.assertEqual(staff_choices, INVOICE_STATUS_PM_CHOICES)

        finance1_choices = invoice_status_user_choices(finance1)
        self.assertEqual(finance1_choices, INVOICE_STATUS_FINANCE_1_CHOICES)

        finance2_choices = invoice_status_user_choices(finance2)
        self.assertEqual(finance2_choices, INVOICE_STATUS_FINANCE_2_CHOICES)

    def test_staff_can_delete_from_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        staff = StaffFactory()

        self.assertTrue(invoice.can_user_delete(staff))

    def test_staff_cant_delete_from_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        staff = StaffFactory()

        self.assertFalse(invoice.can_user_delete(staff))

    def test_staff_cant_delete_from_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        staff = StaffFactory()

        self.assertFalse(invoice.can_user_delete(staff))

    def test_staff_cant_delete_from_paid(self):
        invoice = InvoiceFactory(status=PAID)
        staff = StaffFactory()

        self.assertFalse(invoice.can_user_delete(staff))

    def test_staff_cant_delete_from_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        staff = StaffFactory()

        self.assertFalse(invoice.can_user_delete(staff))

    def test_can_user_delete_from_submitted(self):
        invoice = InvoiceFactory(status=SUBMITTED)
        user = ApplicantFactory()

        self.assertTrue(invoice.can_user_delete(user))

    def test_user_cant_delete_from_resubmitted(self):
        invoice = InvoiceFactory(status=RESUBMITTED)
        user = ApplicantFactory()

        self.assertFalse(invoice.can_user_delete(user))

    def test_user_cant_delete_from_changes_requested(self):
        invoice = InvoiceFactory(status=CHANGES_REQUESTED_BY_STAFF)
        user = ApplicantFactory()

        self.assertFalse(invoice.can_user_delete(user))

    def test_user_cant_delete_from_paid(self):
        invoice = InvoiceFactory(status=PAID)
        user = ApplicantFactory()

        self.assertFalse(invoice.can_user_delete(user))

    def test_user_cant_delete_from_declined(self):
        invoice = InvoiceFactory(status=DECLINED)
        user = ApplicantFactory()

        self.assertFalse(invoice.can_user_delete(user))

    def test_paid_value_used_when_no_paid_value(self):
        invoice = InvoiceFactory(
            paid_value=None,
        )
        self.assertNotEqual(invoice.value, Decimal('1'))

    def test_paid_value_overrides_paid_value(self):
        invoice = InvoiceFactory(
            paid_value=Decimal('2'),
        )
        self.assertEqual(invoice.value, Decimal('2'))

        invoice = InvoiceFactory(
            paid_value=Decimal('2'),
        )
        self.assertEqual(invoice.value, Decimal('2'))

    def test_deliverables_total_amount(self):
        deliverable = DeliverableFactory(unit_price=100)
        invoice_deliverable = InvoiceDeliverableFactory(deliverable=deliverable, quantity=2)
        self.assertEqual(invoice_deliverable.deliverable.unit_price, 100.00)

        invoice = InvoiceFactory(status=APPROVED_BY_STAFF)
        invoice.deliverables.add(invoice_deliverable)
        self.assertEqual(invoice.deliverables_total_amount['total'], 200.00)

    def test_staff_can_change_status(self):
        statuses = [SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_change_status(user))

    def test_staff_cant_change_status(self):
        statuses = [
            APPROVED_BY_STAFF, APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2,
            CHANGES_REQUESTED_BY_FINANCE_2, DECLINED, PAID
        ]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_change_status(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance1_can_change_status_with_extended_flow(self):
        statuses = [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_2]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_change_status(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=False)
    def test_finance1_can_change_status(self):
        statuses = [APPROVED_BY_STAFF, APPROVED_BY_FINANCE_1, CONVERTED]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_change_status(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance1_cant_change_status_with_extended_flow(self):
        statuses = [
            APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2, CHANGES_REQUESTED_BY_STAFF,
            CHANGES_REQUESTED_BY_FINANCE_1, DECLINED, PAID, RESUBMITTED, SUBMITTED
        ]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_change_status(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=False)
    def test_finance1_cant_change_status(self):
        statuses = [
            CHANGES_REQUESTED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1,
            DECLINED, PAID, RESUBMITTED, SUBMITTED
        ]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_change_status(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_can_change_status_with_extended_flow(self):
        statuses = [APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2, CONVERTED]
        user = Finance2Factory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_change_status(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_cant_change_status(self):
        statuses = [
            APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1, CHANGES_REQUESTED_BY_FINANCE_2,
            CHANGES_REQUESTED_BY_STAFF, DECLINED, PAID, RESUBMITTED, SUBMITTED
        ]
        user = Finance2Factory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_change_status(user))

    def test_applicant_can_edit_invoice(self):
        statuses = [CHANGES_REQUESTED_BY_STAFF, RESUBMITTED, SUBMITTED]
        user = ApplicantFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit(user))

    def test_applicant_cant_edit_invoice(self):
        statuses = [
            APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2, APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1,
            CHANGES_REQUESTED_BY_FINANCE_2, DECLINED, PAID
        ]
        user = ApplicantFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit(user))

    def test_staff_can_edit_invoice(self):
        statuses = [SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE_1]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit(user))

    def test_staff_cant_edit_invoice(self):
        statuses = [
            APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2, APPROVED_BY_STAFF,
            CHANGES_REQUESTED_BY_FINANCE_2, CHANGES_REQUESTED_BY_STAFF, DECLINED, PAID
        ]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit(user))

    def test_applicant_cant_complete_required_checks(self):
        statuses = [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_2]
        user = ApplicantFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_complete_required_checks(user))

    def test_staff_cant_complete_required_checks(self):
        statuses = [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_2]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_complete_required_checks(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance1_can_complete_required_checks_with_extended_flow(self):
        statuses = [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_2]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_complete_required_checks(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=False)
    def test_finance1_can_complete_required_checks(self):
        statuses = [APPROVED_BY_STAFF]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_complete_required_checks(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_cant_complete_required_checks(self):
        statuses = [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_2]
        user = Finance2Factory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_complete_required_checks(user))

    def test_applicant_cant_view_required_checks(self):
        user = ApplicantFactory()
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        self.assertFalse(invoice.can_user_view_required_checks(user))

    def test_staff_cant_view_required_checks(self):
        user = StaffFactory()
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        self.assertFalse(invoice.can_user_view_required_checks(user))

    def test_finance1_can_view_required_checks(self):
        user = FinanceFactory()
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        self.assertTrue(invoice.can_user_view_required_checks(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_can_view_required_checks(self):
        user = Finance2Factory()
        invoice = InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        self.assertTrue(invoice.can_user_view_required_checks(user))

    def test_applicant_cant_edit_deliverables(self):
        statuses = [
            SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1,
            APPROVED_BY_FINANCE_1, CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2, DECLINED, PAID
        ]
        user = ApplicantFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit_deliverables(user))

    def test_staff_can_edit_deliverables(self):
        statuses = [SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE_1]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit_deliverables(user))

    def test_staff_cant_edit_deliverables(self):
        statuses = [
            APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2, APPROVED_BY_STAFF,
            CHANGES_REQUESTED_BY_FINANCE_2, CHANGES_REQUESTED_BY_STAFF, DECLINED, PAID
        ]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit_deliverables(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance1_can_edit_deliverables_with_extended_flow(self):
        statuses = [APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_2]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit_deliverables(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=False)
    def test_finance1_can_edit_deliverables(self):
        statuses = [APPROVED_BY_STAFF]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit_deliverables(user))

    def test_finance1_cant_edit_deliverables(self):
        statuses = [
            APPROVED_BY_FINANCE_1, APPROVED_BY_FINANCE_2, CHANGES_REQUESTED_BY_FINANCE_1, CHANGES_REQUESTED_BY_STAFF,
            DECLINED, PAID, SUBMITTED, RESUBMITTED,
        ]
        user = FinanceFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit_deliverables(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_can_edit_deliverables(self):
        statuses = [APPROVED_BY_FINANCE_1]
        user = Finance2Factory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit_deliverables(user))

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_finance2_cant_edit_deliverables(self):
        statuses = [
            APPROVED_BY_FINANCE_2, APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1,
            CHANGES_REQUESTED_BY_FINANCE_2, CHANGES_REQUESTED_BY_STAFF, DECLINED, PAID, SUBMITTED, RESUBMITTED
        ]
        user = Finance2Factory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit_deliverables(user))


class TestInvoiceQueryset(TestCase):
    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_in_progress_with_extended_workflow(self):
        InvoiceFactory(status=SUBMITTED)
        InvoiceFactory(status=APPROVED_BY_STAFF)
        InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_2)
        InvoiceFactory(status=DECLINED)
        self.assertEqual(Invoice.objects.in_progress().count(), 3)

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_in_progress(self):
        InvoiceFactory(status=SUBMITTED)
        InvoiceFactory(status=APPROVED_BY_STAFF)
        InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_1)
        InvoiceFactory(status=DECLINED)
        self.assertEqual(Invoice.objects.in_progress().count(), 3)

    def test_approved_by_staff(self):
        InvoiceFactory(status=APPROVED_BY_STAFF)
        self.assertEqual(Invoice.objects.approved_by_staff().count(), 1)

    def test_approved_by_finance_1(self):
        InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        self.assertEqual(Invoice.objects.approved_by_finance_1().count(), 1)

    @override_settings(INVOICE_EXTENDED_WORKFLOW=True)
    def test_for_finance_1_with_extended_flow(self):
        InvoiceFactory(status=APPROVED_BY_STAFF)
        InvoiceFactory(status=CHANGES_REQUESTED_BY_FINANCE_2)
        InvoiceFactory(status=SUBMITTED)
        self.assertEqual(Invoice.objects.for_finance_1().count(), 2)

    @override_settings(INVOICE_EXTENDED_WORKFLOW=False)
    def test_for_finance_1(self):
        InvoiceFactory(status=APPROVED_BY_STAFF)
        InvoiceFactory(status=APPROVED_BY_FINANCE_1)
        InvoiceFactory(status=SUBMITTED)
        self.assertEqual(Invoice.objects.for_finance_1().count(), 2)

    def test_rejected(self):
        InvoiceFactory(status=DECLINED)
        InvoiceFactory(status=SUBMITTED)
        self.assertEqual(Invoice.objects.rejected().count(), 1)

    def test_not_rejected(self):
        InvoiceFactory(status=DECLINED)
        InvoiceFactory(status=SUBMITTED)
        self.assertEqual(Invoice.objects.not_rejected().count(), 1)

    def test_get_totals(self):
        InvoiceFactory(paid_value=20)
        InvoiceFactory(paid_value=10, status=PAID)
        self.assertEqual(Invoice.objects.paid_value(), 10)
        self.assertEqual(Invoice.objects.unpaid_value(), 20)

    def test_get_totals_no_value(self):
        self.assertEqual(Invoice.objects.paid_value(), 0)
        self.assertEqual(Invoice.objects.unpaid_value(), 0)


class TestReportConfig(TestCase):
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

    def test_last_report_gets_report_in_past(self):
        config = ReportConfigFactory()
        past_report = ReportFactory(
            project=config.project,
            end_date=self.today - relativedelta(days=3),
        )
        self.assertEqual(past_report, config.last_report())

    def test_last_report_gets_submitted_report_in_past(self):
        config = ReportConfigFactory()
        past_report = ReportFactory(
            project=config.project,
            end_date=self.today - relativedelta(days=3),
            is_submitted=True,
        )
        self.assertEqual(past_report, config.last_report())

    def test_last_report_gets_skipped(self):
        config = ReportConfigFactory()
        skipped_report = ReportFactory(
            project=config.project,
            end_date=self.today + relativedelta(days=3),
            skipped=True,
        )
        self.assertEqual(skipped_report, config.last_report())

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
        # Separate day from month for case where start date + 1 month would exceed next month
        # length (31st Oct to 30th Nov)
        # combined => 31th + 1 month = 30th - 1 day = 29th (wrong)
        # separate => 31th - 1 day = 30th + 1 month = 30th (correct)
        next_due = report.project.start_date - relativedelta(days=1) + relativedelta(months=1)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(report.end_date, next_due)

    def test_no_report_creates_report_not_in_past(self):
        config = ReportConfigFactory(schedule_start=self.today - relativedelta(months=3))
        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(report.end_date, self.today)

    def test_no_report_creates_report_if_current_skipped(self):
        config = ReportConfigFactory()
        skipped_report = ReportFactory(end_date=self.today + relativedelta(days=3))
        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 2)
        self.assertNotEqual(skipped_report, report)

    def test_no_report_schedule_in_future_creates_report(self):
        config = ReportConfigFactory(schedule_start=self.today + relativedelta(days=2))
        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(report.end_date, self.today + relativedelta(days=2))

    def test_past_due_report_creates_report(self):
        config = ReportConfigFactory(schedule_start=self.today - relativedelta(days=2))
        ReportFactory(project=config.project, end_date=self.today - relativedelta(days=1))

        # Separate day from month for case where start date + 1 month would exceed next month
        # length (31st Oct to 30th Nov)
        # combined => 31th + 1 month = 30th - 1 day = 29th (wrong)
        # separate => 31th - 1 day = 30th + 1 month = 30th (correct)
        next_due = self.today - relativedelta(days=1) + relativedelta(months=1)

        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 2)
        self.assertEqual(report.end_date, next_due)

    def test_today_schedule_gets_report_today(self):
        config = ReportConfigFactory(schedule_start=self.today)
        self.assertEqual(config.current_due_report().end_date, self.today)

    def test_past_due_report_future_schedule_creates_report(self):
        config = ReportConfigFactory(schedule_start=self.today + relativedelta(days=3))
        ReportFactory(project=config.project, end_date=self.today - relativedelta(days=1))

        report = config.current_due_report()
        self.assertEqual(Report.objects.count(), 2)
        self.assertEqual(report.end_date, self.today + relativedelta(days=3))

    def test_submitted_report_unaffected(self):
        config = ReportConfigFactory()
        report = ReportFactory(is_submitted=True, project=config.project, end_date=self.today + relativedelta(days=1))
        next_report = config.current_due_report()
        self.assertNotEqual(report, next_report)

    def test_past_due(self):
        report = ReportFactory(past_due=True)
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [report], transform=lambda x: x)

    def test_past_due_has_drafts(self):
        report = ReportFactory(past_due=True, is_draft=True)
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [report], transform=lambda x: x)

    def test_past_due_no_submitted(self):
        report = ReportFactory(is_submitted=True, past_due=True)
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [], transform=lambda x: x)

    def test_past_due_no_future(self):
        report = ReportFactory(end_date=self.today + relativedelta(days=1))
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [], transform=lambda x: x)

    def test_past_due_no_skipped(self):
        report = ReportFactory(skipped=True, past_due=True)
        config = report.project.report_config
        self.assertQuerysetEqual(config.past_due_reports(), [], transform=lambda x: x)


class TestReport(TestCase):
    @property
    def today(self):
        return timezone.now().date()

    def from_today(self, days):
        return self.today + relativedelta(days=days)

    def test_not_late_if_one_ahead(self):
        report = ReportFactory(end_date=self.from_today(-3))
        ReportFactory(project=report.project)
        self.assertFalse(report.is_very_late)

    def test_late_if_two_weeks_behind(self):
        report = ReportFactory(end_date=self.from_today(-15))
        self.assertTrue(report.is_very_late)

    def test_not_late_if_two_ahead_but_one_in_future(self):
        report = ReportFactory(end_date=self.from_today(-3))
        ReportFactory(project=report.project)
        ReportFactory(end_date=self.from_today(2), project=report.project)
        self.assertFalse(report.is_very_late)

    def test_start_date(self):
        yesterday = self.from_today(-1)
        ReportFactory(end_date=yesterday)
        report = ReportFactory(end_date=self.from_today(1))
        self.assertEqual(report.start_date, self.today)

    def test_start_date_with_submitted(self):
        yesterday = self.from_today(-1)
        ReportFactory(end_date=yesterday)
        report = ReportFactory(end_date=self.from_today(1), is_submitted=True)
        self.assertEqual(report.start_date, self.today)

    def test_queryset_done_includes_submitted(self):
        report = ReportFactory(is_submitted=True)
        self.assertQuerysetEqual(Report.objects.done(), [report], transform=lambda x: x)

    def test_queryset_done_includes_skipped(self):
        report = ReportFactory(skipped=True)
        self.assertQuerysetEqual(Report.objects.done(), [report], transform=lambda x: x)

    def test_queryset_done_doesnt_includes_draft(self):
        ReportFactory(is_draft=True)
        self.assertQuerysetEqual(Report.objects.done(), [], transform=lambda x: x)

    def test_queryset_done_doesnt_includes_to_do(self):
        ReportFactory()
        self.assertQuerysetEqual(Report.objects.done(), [], transform=lambda x: x)
