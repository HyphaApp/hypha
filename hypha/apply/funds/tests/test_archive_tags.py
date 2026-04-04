"""Tests for funds/templatetags/archive_tags.py and other simple template tags."""

from django.test import SimpleTestCase, TestCase, override_settings

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import (
    ApplicantFactory,
    ReviewerFactory,
    StaffFactory,
)

from ..templatetags.archive_tags import join_with_commas
from ..templatetags.primaryactions_tags import display_coapplicant_section
from ..templatetags.workflow_tags import has_review_perm, show_applicant_identity


class TestJoinWithCommas(SimpleTestCase):
    def test_empty_list_returns_empty_string(self):
        self.assertEqual(join_with_commas([]), "")

    def test_single_item(self):
        self.assertEqual(join_with_commas(["apples"]), "apples")

    def test_two_items(self):
        self.assertEqual(join_with_commas(["apples", "oranges"]), "apples and oranges")

    def test_three_items(self):
        result = join_with_commas(["apples", "oranges", "pears"])
        self.assertEqual(result, "apples, oranges and pears")

    def test_four_items(self):
        result = join_with_commas(["a", "b", "c", "d"])
        self.assertEqual(result, "a, b, c and d")

    def test_works_with_non_string_objects(self):
        class Fruit:
            def __init__(self, name):
                self.name = name

            def __str__(self):
                return self.name

        result = join_with_commas([Fruit("apple"), Fruit("banana")])
        self.assertEqual(result, "apple and banana")

    def test_none_returns_empty_string(self):
        self.assertEqual(join_with_commas(None), "")


class TestShowApplicantIdentity(TestCase):
    @override_settings(HIDE_IDENTITY_FROM_REVIEWERS=False)
    def test_always_shows_when_setting_disabled(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[reviewer]
        )
        self.assertTrue(show_applicant_identity(submission, reviewer))

    @override_settings(HIDE_IDENTITY_FROM_REVIEWERS=True)
    def test_hides_from_reviewer_assigned_to_submission(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[reviewer]
        )
        self.assertFalse(show_applicant_identity(submission, reviewer))

    @override_settings(HIDE_IDENTITY_FROM_REVIEWERS=True)
    def test_shows_to_staff_even_when_setting_enabled(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2
        )
        # Staff is org_faculty, so identity is shown
        self.assertTrue(show_applicant_identity(submission, staff))

    @override_settings(HIDE_IDENTITY_FROM_REVIEWERS=True)
    def test_shows_to_reviewer_not_assigned_to_submission(self):
        reviewer = ReviewerFactory()
        # Different reviewer — not in submission.reviewers
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2
        )
        self.assertTrue(show_applicant_identity(submission, reviewer))


class TestHasReviewPerm(TestCase):
    def test_reviewer_in_external_review_has_perm(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[reviewer]
        )
        self.assertTrue(has_review_perm(reviewer, submission))

    def test_archived_submission_has_no_review_perm(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory(is_archive=True)
        self.assertFalse(has_review_perm(reviewer, submission))

    def test_applicant_has_no_review_perm(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        self.assertFalse(has_review_perm(applicant, submission))


class TestDisplayCoapplicantSection(TestCase):
    def test_staff_can_view_coapplicants(self):
        staff = StaffFactory()
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        self.assertTrue(display_coapplicant_section(staff, submission))

    def test_owner_can_view_coapplicants(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        self.assertTrue(display_coapplicant_section(applicant, submission))

    def test_unrelated_applicant_cannot_view_coapplicants(self):
        other = ApplicantFactory()
        submission = ApplicationSubmissionFactory()
        self.assertFalse(display_coapplicant_section(other, submission))
