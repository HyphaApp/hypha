"""Tests for activity/adapters/utils.py pure functions."""

from django.test import SimpleTestCase, TestCase

from hypha.apply.activity.options import MESSAGES
from hypha.apply.projects.models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
    SUBMITTED,
)

from ..adapters.utils import (
    group_reviewers,
    is_invoice_public_transition,
    is_ready_for_review,
    is_reviewer_update,
    is_transition,
    reviewers_message,
)


class TestIsTransition(SimpleTestCase):
    def test_transition_message_returns_true(self):
        self.assertTrue(is_transition(MESSAGES.TRANSITION))

    def test_batch_transition_returns_true(self):
        self.assertTrue(is_transition(MESSAGES.BATCH_TRANSITION))

    def test_comment_message_returns_false(self):
        self.assertFalse(is_transition(MESSAGES.COMMENT))

    def test_new_submission_returns_false(self):
        self.assertFalse(is_transition(MESSAGES.NEW_SUBMISSION))


class TestIsReadyForReview(SimpleTestCase):
    def test_ready_for_review_returns_true(self):
        self.assertTrue(is_ready_for_review(MESSAGES.READY_FOR_REVIEW))

    def test_batch_ready_for_review_returns_true(self):
        self.assertTrue(is_ready_for_review(MESSAGES.BATCH_READY_FOR_REVIEW))

    def test_transition_returns_false(self):
        self.assertFalse(is_ready_for_review(MESSAGES.TRANSITION))


class TestIsReviewerUpdate(SimpleTestCase):
    def test_reviewers_updated_returns_true(self):
        self.assertTrue(is_reviewer_update(MESSAGES.REVIEWERS_UPDATED))

    def test_batch_reviewers_updated_returns_true(self):
        self.assertTrue(is_reviewer_update(MESSAGES.BATCH_REVIEWERS_UPDATED))

    def test_comment_returns_false(self):
        self.assertFalse(is_reviewer_update(MESSAGES.COMMENT))


class TestIsInvoicePublicTransition(TestCase):
    def _invoice(self, status):
        from unittest.mock import MagicMock

        invoice = MagicMock()
        invoice.status = status
        return invoice

    def test_submitted_is_public(self):
        self.assertTrue(is_invoice_public_transition(self._invoice(SUBMITTED)))

    def test_resubmitted_is_public(self):
        self.assertTrue(is_invoice_public_transition(self._invoice(RESUBMITTED)))

    def test_changes_requested_is_public(self):
        self.assertTrue(
            is_invoice_public_transition(self._invoice(CHANGES_REQUESTED_BY_STAFF))
        )

    def test_declined_is_public(self):
        self.assertTrue(is_invoice_public_transition(self._invoice(DECLINED)))

    def test_paid_is_public(self):
        self.assertTrue(is_invoice_public_transition(self._invoice(PAID)))

    def test_payment_failed_is_public(self):
        self.assertTrue(is_invoice_public_transition(self._invoice(PAYMENT_FAILED)))

    def test_approved_by_finance_is_public(self):
        self.assertTrue(
            is_invoice_public_transition(self._invoice(APPROVED_BY_FINANCE))
        )

    def test_approved_by_staff_is_not_public(self):
        self.assertFalse(is_invoice_public_transition(self._invoice(APPROVED_BY_STAFF)))


class TestGroupReviewers(SimpleTestCase):
    def _reviewer(self, role, name):
        from unittest.mock import MagicMock

        r = MagicMock()
        r.role = role
        r.reviewer = name
        return r

    def test_groups_by_role(self):
        reviewers = [
            self._reviewer("lead", "Alice"),
            self._reviewer("lead", "Bob"),
            self._reviewer("external", "Carol"),
        ]
        groups = group_reviewers(reviewers)
        self.assertEqual(len(groups["lead"]), 2)
        self.assertEqual(len(groups["external"]), 1)

    def test_empty_list_returns_empty_dict(self):
        groups = group_reviewers([])
        self.assertEqual(dict(groups), {})

    def test_none_role_is_valid_key(self):
        reviewers = [self._reviewer(None, "Alice")]
        groups = group_reviewers(reviewers)
        self.assertIn(None, groups)


class TestReviewersMessage(SimpleTestCase):
    def _reviewer(self, role, name):
        from unittest.mock import MagicMock

        r = MagicMock()
        r.role = role
        r.reviewer.__str__ = lambda self: name
        return r

    def test_reviewer_without_role_no_role_suffix(self):
        reviewers = [self._reviewer(None, "Alice")]
        messages = reviewers_message(reviewers)
        self.assertEqual(len(messages), 1)
        self.assertIn("Alice", messages[0])
        self.assertNotIn(" as ", messages[0])

    def test_reviewer_with_role_includes_suffix(self):
        reviewers = [self._reviewer("Lead", "Bob")]
        messages = reviewers_message(reviewers)
        self.assertEqual(len(messages), 1)
        self.assertIn(" as Lead", messages[0])

    def test_multiple_roles_produce_multiple_messages(self):
        reviewers = [
            self._reviewer("Lead", "Alice"),
            self._reviewer("External", "Bob"),
        ]
        messages = reviewers_message(reviewers)
        self.assertEqual(len(messages), 2)

    def test_empty_reviewers_returns_empty_list(self):
        self.assertEqual(reviewers_message([]), [])
