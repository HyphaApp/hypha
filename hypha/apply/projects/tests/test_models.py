from decimal import Decimal

from django.test import TestCase

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    FinanceFactory,
    StaffFactory,
)

from ..models.payment import (
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
from .factories import InvoiceFactory


class TestProjectModel(TestCase):
    def test_create_from_submission(self):
        submission = ApplicationSubmissionFactory()
        project = Project.create_from_submission(submission)
        self.assertEqual(project.submission, submission)
        self.assertEqual(project.title, submission.title)
        self.assertEqual(project.user, submission.user)


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
