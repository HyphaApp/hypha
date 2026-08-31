"""Tests for activity/templatetags/activity_tags.py."""

from django.test import SimpleTestCase, TestCase, override_settings

from hypha.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..models import ALL, REVIEWER, TEAM
from ..templatetags.activity_tags import (
    email_name,
    lowerfirst,
    source_type,
    visibility_display,
)


class TestLowerfirst(SimpleTestCase):
    def test_lowercases_first_character(self):
        self.assertEqual(lowerfirst("Hello"), "hello")

    def test_preserves_rest_of_string(self):
        self.assertEqual(lowerfirst("Hello World"), "hello World")

    def test_already_lowercase_unchanged(self):
        self.assertEqual(lowerfirst("hello"), "hello")

    def test_empty_string_returns_empty(self):
        self.assertEqual(lowerfirst(""), "")

    def test_single_character(self):
        self.assertEqual(lowerfirst("A"), "a")


class TestEmailName(SimpleTestCase):
    def test_extracts_username_from_email(self):
        self.assertEqual(email_name("alice@example.com"), "alice")

    def test_returns_string_unchanged_if_no_at_sign(self):
        self.assertEqual(email_name("alice"), "alice")

    def test_returns_non_string_unchanged(self):
        self.assertEqual(email_name(42), 42)

    def test_returns_none_unchanged(self):
        self.assertIsNone(email_name(None))

    def test_extracts_first_part_only(self):
        self.assertEqual(email_name("first.last@domain.org"), "first.last")


class TestSourceType(SimpleTestCase):
    def test_submission_variant_returns_submission(self):
        self.assertEqual(source_type("application submission"), "Submission")

    def test_exact_submission_returns_submission(self):
        self.assertEqual(source_type("submission"), "Submission")

    def test_non_submission_capitalizes_first_letter(self):
        self.assertEqual(source_type("project"), "Project")

    def test_none_returns_none_string(self):
        self.assertEqual(source_type(None), "None")

    def test_empty_string_returns_empty(self):
        self.assertEqual(source_type(""), "")


class TestVisibilityDisplay(TestCase):
    def test_team_visibility_for_staff_returns_team(self):
        staff = StaffFactory()
        result = visibility_display(TEAM, staff)
        self.assertEqual(result, TEAM)

    @override_settings(ORG_SHORT_NAME="OTF")
    def test_team_visibility_for_applicant_includes_org_name(self):
        applicant = ApplicantFactory()
        result = visibility_display(TEAM, applicant)
        self.assertIn("OTF", result)
        self.assertIn(str(TEAM), result)

    def test_all_visibility_returns_all(self):
        staff = StaffFactory()
        result = visibility_display(ALL, staff)
        self.assertEqual(result, ALL)

    def test_reviewer_visibility_for_staff_includes_team(self):
        staff = StaffFactory()
        result = visibility_display(REVIEWER, staff)
        # REVIEWER is not TEAM or ALL → "reviewers + team"
        self.assertIn(str(REVIEWER), result)
        self.assertIn(str(TEAM), result)

    @override_settings(ORG_SHORT_NAME="OTF")
    def test_reviewer_visibility_for_applicant_includes_org_team(self):
        applicant = ApplicantFactory()
        result = visibility_display(REVIEWER, applicant)
        self.assertIn(str(REVIEWER), result)
        self.assertIn("OTF", result)
