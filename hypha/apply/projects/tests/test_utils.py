"""Tests for projects/utils.py pure functions."""

import pytest
from django.test import TestCase

from ..constants import (
    INT_DECLINED,
    INT_FINANCE_PENDING,
    INT_ORG_PENDING,
    INT_PAID,
    INT_PAYMENT_FAILED,
    INT_REQUEST_FOR_CHANGE,
    INT_STAFF_PENDING,
    INT_VENDOR_PENDING,
)
from ..models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
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
from ..utils import (
    get_invoice_public_status,
    get_invoice_table_status,
    get_project_public_status,
    get_project_status_choices,
    get_project_status_display_value,
)
from .factories import PAFReviewerRoleFactory


class TestGetInvoicePublicStatus(TestCase):
    def test_submitted_is_pending_approval(self):
        self.assertEqual(str(get_invoice_public_status(SUBMITTED)), "Pending approval")

    def test_resubmitted_is_pending_approval(self):
        self.assertEqual(
            str(get_invoice_public_status(RESUBMITTED)), "Pending approval"
        )

    def test_approved_by_staff_is_pending_approval(self):
        self.assertEqual(
            str(get_invoice_public_status(APPROVED_BY_STAFF)), "Pending approval"
        )

    def test_changes_requested_by_finance_is_pending_approval(self):
        self.assertEqual(
            str(get_invoice_public_status(CHANGES_REQUESTED_BY_FINANCE)),
            "Pending approval",
        )

    def test_approved_by_finance_is_approved(self):
        self.assertEqual(
            str(get_invoice_public_status(APPROVED_BY_FINANCE)), "Approved"
        )

    def test_changes_requested_by_staff_is_request_for_change(self):
        self.assertIn(
            "change", str(get_invoice_public_status(CHANGES_REQUESTED_BY_STAFF)).lower()
        )

    def test_declined_is_declined(self):
        self.assertEqual(str(get_invoice_public_status(DECLINED)), "Declined")

    def test_paid_is_paid(self):
        self.assertEqual(str(get_invoice_public_status(PAID)), "Paid")

    def test_payment_failed_is_payment_failed(self):
        self.assertEqual(
            str(get_invoice_public_status(PAYMENT_FAILED)), "Payment failed"
        )


class TestGetInvoiceTableStatus(TestCase):
    def test_submitted_is_staff_pending_for_staff(self):
        self.assertEqual(get_invoice_table_status(SUBMITTED), INT_STAFF_PENDING)

    def test_submitted_is_org_pending_for_applicant(self):
        self.assertEqual(
            get_invoice_table_status(SUBMITTED, is_applicant=True), INT_ORG_PENDING
        )

    def test_resubmitted_is_staff_pending_for_staff(self):
        self.assertEqual(get_invoice_table_status(RESUBMITTED), INT_STAFF_PENDING)

    def test_resubmitted_is_org_pending_for_applicant(self):
        self.assertEqual(
            get_invoice_table_status(RESUBMITTED, is_applicant=True), INT_ORG_PENDING
        )

    def test_changes_requested_by_staff_is_vendor_pending_for_staff(self):
        self.assertEqual(
            get_invoice_table_status(CHANGES_REQUESTED_BY_STAFF), INT_VENDOR_PENDING
        )

    def test_changes_requested_by_staff_is_request_for_change_for_applicant(self):
        self.assertEqual(
            get_invoice_table_status(CHANGES_REQUESTED_BY_STAFF, is_applicant=True),
            INT_REQUEST_FOR_CHANGE,
        )

    def test_approved_by_staff_is_finance_pending_for_staff(self):
        self.assertEqual(
            get_invoice_table_status(APPROVED_BY_STAFF), INT_FINANCE_PENDING
        )

    def test_approved_by_staff_is_org_pending_for_applicant(self):
        self.assertEqual(
            get_invoice_table_status(APPROVED_BY_STAFF, is_applicant=True),
            INT_ORG_PENDING,
        )

    def test_changes_requested_by_finance_is_finance_pending_for_staff(self):
        self.assertEqual(
            get_invoice_table_status(CHANGES_REQUESTED_BY_FINANCE), INT_FINANCE_PENDING
        )

    def test_paid_is_paid(self):
        self.assertEqual(get_invoice_table_status(PAID), INT_PAID)

    def test_declined_is_declined(self):
        self.assertEqual(get_invoice_table_status(DECLINED), INT_DECLINED)

    def test_payment_failed_is_payment_failed(self):
        self.assertEqual(get_invoice_table_status(PAYMENT_FAILED), INT_PAYMENT_FAILED)


class TestGetProjectStatusChoices(TestCase):
    def test_excludes_internal_approval_when_no_paf_roles(self):
        choices = get_project_status_choices()
        statuses = [s for s, _ in choices]
        self.assertNotIn(INTERNAL_APPROVAL, statuses)

    def test_includes_internal_approval_when_paf_roles_exist(self):
        PAFReviewerRoleFactory()
        choices = get_project_status_choices()
        statuses = [s for s, _ in choices]
        self.assertIn(INTERNAL_APPROVAL, statuses)

    def test_always_includes_common_statuses(self):
        choices = get_project_status_choices()
        statuses = [s for s, _ in choices]
        for status in [DRAFT, CONTRACTING, INVOICING_AND_REPORTING, CLOSING, COMPLETE]:
            self.assertIn(status, statuses)


class TestGetProjectPublicStatus(TestCase):
    @pytest.mark.parametrize(
        "status", [DRAFT, CONTRACTING, INVOICING_AND_REPORTING, CLOSING, COMPLETE]
    )
    def test_returns_string_for_all_statuses(self):
        for status in [DRAFT, CONTRACTING, INVOICING_AND_REPORTING, CLOSING, COMPLETE]:
            result = get_project_public_status(status)
            self.assertIsNotNone(result)


class TestGetProjectStatusDisplayValue(TestCase):
    def test_returns_display_for_draft(self):
        result = get_project_status_display_value(DRAFT)
        self.assertIsNotNone(result)
        self.assertIsInstance(str(result), str)
