import datetime
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from wagtail.models import ModelLogEntry

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    FinanceFactory,
    StaffFactory,
)

from ..models.disbursement import Disbursement
from ..models.invoice import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    INVOICE_STATUS_FINANCE_1_CHOICES,
    INVOICE_STATUS_PM_CHOICES,
    PAID,
    RESUBMITTED,
    SUBMITTED,
    Invoice,
    invoice_status_user_choices,
)
from ..models.project import Project
from .factories import ContractFactory, InvoiceFactory


class TestProjectModel(TestCase):
    def test_create_from_submission(self):
        submission = ApplicationSubmissionFactory()
        project = Project.create_from_submission(submission)
        self.assertEqual(project.submission, submission)
        self.assertEqual(project.title, submission.title)
        self.assertEqual(project.user, submission.user)

    def test_create_from_submission_with_title(self):
        submission = ApplicationSubmissionFactory()
        project = Project.create_from_submission(submission, title="Hardware")
        self.assertEqual(project.title, "Hardware")

    def test_submission_can_have_multiple_projects(self):
        submission = ApplicationSubmissionFactory()
        first = Project.create_from_submission(submission, title="Hardware")
        second = Project.create_from_submission(submission, title="Travel")

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(
            list(submission.projects.order_by("pk")),
            [first, second],
        )


class TestInvoiceModel(TestCase):
    def test_invoice_status_user_choices(self):
        applicant = ApplicantFactory()
        staff = StaffFactory()
        finance1 = FinanceFactory()
        applicant_choices = invoice_status_user_choices(applicant)
        self.assertEqual(applicant_choices, [])

        staff_choices = invoice_status_user_choices(staff)
        self.assertEqual(staff_choices, INVOICE_STATUS_PM_CHOICES)

        finance1_choices = invoice_status_user_choices(finance1)
        self.assertEqual(finance1_choices, INVOICE_STATUS_FINANCE_1_CHOICES)

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
        user = ApplicantFactory()
        invoice = InvoiceFactory(status=SUBMITTED, project__user=user)
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
        invoice = InvoiceFactory(paid_value=None)
        self.assertNotEqual(invoice.value, Decimal("1"))

    def test_paid_value_overrides_paid_value(self):
        invoice = InvoiceFactory(paid_value=Decimal("2"))
        self.assertEqual(invoice.value, Decimal("2"))

    def test_staff_can_change_status(self):
        statuses = [
            SUBMITTED,
            RESUBMITTED,
            CHANGES_REQUESTED_BY_STAFF,
            CHANGES_REQUESTED_BY_FINANCE,
        ]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_change_status(user))

    def test_staff_cant_change_status(self):
        statuses = [
            APPROVED_BY_STAFF,
            APPROVED_BY_FINANCE,
            DECLINED,
            PAID,
        ]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_change_status(user))

    def test_applicant_can_edit_invoice(self):
        statuses = [CHANGES_REQUESTED_BY_STAFF, RESUBMITTED, SUBMITTED]
        user = ApplicantFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status, project__user=user)
            self.assertTrue(invoice.can_user_edit(user))

    def test_applicant_cant_edit_invoice(self):
        statuses = [
            APPROVED_BY_FINANCE,
            APPROVED_BY_STAFF,
            CHANGES_REQUESTED_BY_FINANCE,
            DECLINED,
            PAID,
        ]
        user = ApplicantFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit(user))

    def test_staff_can_edit_invoice(self):
        statuses = [SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertTrue(invoice.can_user_edit(user))

    def test_staff_cant_edit_invoice(self):
        statuses = [
            APPROVED_BY_FINANCE,
            APPROVED_BY_STAFF,
            CHANGES_REQUESTED_BY_STAFF,
            DECLINED,
            PAID,
        ]
        user = StaffFactory()
        for status in statuses:
            invoice = InvoiceFactory(status=status)
            self.assertFalse(invoice.can_user_edit(user))


class TestInvoiceQueryset(TestCase):
    def test_approved_by_staff(self):
        InvoiceFactory(status=APPROVED_BY_STAFF)
        self.assertEqual(Invoice.objects.approved_by_staff().count(), 1)

    def test_approved_by_finance_1(self):
        InvoiceFactory(status=APPROVED_BY_FINANCE)
        self.assertEqual(Invoice.objects.approved_by_finance_1().count(), 1)

    def test_for_finance_1(self):
        InvoiceFactory(status=APPROVED_BY_STAFF)
        InvoiceFactory(status=APPROVED_BY_FINANCE)
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


class TestDisbursementModel(TestCase):
    """Test values use prime numbers (prime left and right of the decimal
    point) that are unique to this test, and dates several hundred years in
    the future, so a correct assertion is traceable to this test and not a
    coincidence. The system under test (Disbursement) is constructed directly
    via its initializer; factories are used only for its dependencies
    (Contract, Staff), which the test harness owns.
    """

    def test_str_includes_amount_and_date(self):
        contract = ContractFactory()
        disbursement = Disbursement(
            contract=contract,
            amount=Decimal("53.17"),
            date=datetime.date(2525, 7, 19),
        )
        disbursement.save()
        rendered = str(disbursement)
        self.assertIn("53.17", rendered)
        self.assertIn("2525-07-19", rendered)

    def test_negative_amount_allowed_for_repayment(self):
        disbursement = Disbursement(
            contract=ContractFactory(),
            amount=Decimal("-61.13"),
            date=datetime.date(2527, 11, 23),
        )
        disbursement.save()
        disbursement.refresh_from_db()
        self.assertEqual(disbursement.amount, Decimal("-61.13"))

    def test_create_emits_wagtail_create_log_entry(self):
        staff = StaffFactory()
        contract = ContractFactory()
        disbursement = Disbursement(
            contract=contract,
            amount=Decimal("67.19"),
            date=datetime.date(2529, 3, 17),
            updated_by=staff,
        )
        disbursement.save()
        entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Disbursement),
            object_id=disbursement.pk,
        )
        self.assertTrue(entries.exists())
        self.assertEqual(entries.first().action, "wagtail.create")
        self.assertEqual(entries.first().user, staff)

    def test_edit_emits_wagtail_edit_log_entry(self):
        staff = StaffFactory()
        disbursement = Disbursement(
            contract=ContractFactory(),
            amount=Decimal("71.23"),
            date=datetime.date(2537, 1, 7),
            updated_by=staff,
        )
        disbursement.save()
        disbursement.amount = Decimal("73.29")
        disbursement.updated_by = staff
        disbursement.save()
        entries = ModelLogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Disbursement),
            object_id=disbursement.pk,
        )
        # create then edit each emit an entry; assert both are present and the
        # edit is the most recent (ModelLogEntry defaults to newest-first).
        self.assertEqual(entries.count(), 2)
        self.assertEqual(
            set(entries.values_list("action", flat=True)),
            {"wagtail.create", "wagtail.edit"},
        )
        self.assertEqual(entries.first().action, "wagtail.edit")

    def test_contract_disbursements_related_name(self):
        contract = ContractFactory()
        Disbursement(
            contract=contract, amount=Decimal("79.31"), date=datetime.date(2539, 4, 3)
        ).save()
        Disbursement(
            contract=contract,
            amount=Decimal("-83.37"),
            date=datetime.date(2539, 4, 3),
        ).save()
        # Sum() over the related manager nets negatives (repayments) correctly.
        total = sum(d.amount for d in contract.disbursements.all())
        self.assertEqual(total, Decimal("-4.06"))

    def test_updated_by_changes_on_edit_while_created_by_does_not(self):
        creator = StaffFactory()
        editor = StaffFactory()
        disbursement = Disbursement(
            contract=ContractFactory(),
            amount=Decimal("89.41"),
            date=datetime.date(2531, 5, 13),
            created_by=creator,
            updated_by=creator,
        )
        disbursement.save()
        disbursement.amount = Decimal("97.11")
        disbursement.updated_by = editor
        disbursement.save()
        disbursement.refresh_from_db()
        self.assertEqual(disbursement.created_by, creator)
        self.assertEqual(disbursement.updated_by, editor)

    def test_notes_field_persisted(self):
        disbursement = Disbursement(
            contract=ContractFactory(),
            amount=Decimal("101.03"),
            date=datetime.date(2533, 9, 29),
            notes="Wire transfer for the reporting period.",
        )
        disbursement.save()
        disbursement.refresh_from_db()
        self.assertEqual(disbursement.notes, "Wire transfer for the reporting period.")
