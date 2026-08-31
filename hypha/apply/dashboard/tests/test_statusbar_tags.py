"""Tests for dashboard/templatetags/dashboard_statusbar_tags.py."""

from django.test import TestCase

from hypha.apply.projects.models.project import (
    CONTRACTING,
    DRAFT,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
    PROJECT_PUBLIC_STATUSES,
    PROJECT_STATUS_CHOICES,
)
from hypha.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..templatetags.dashboard_statusbar_tags import project_status_bar


class TestProjectStatusBar(TestCase):
    def test_staff_sees_full_status_choices(self):
        staff = StaffFactory()
        result = project_status_bar(DRAFT, staff)
        self.assertEqual(result["statuses"], PROJECT_STATUS_CHOICES)

    def test_applicant_sees_public_statuses(self):
        applicant = ApplicantFactory()
        result = project_status_bar(DRAFT, applicant)
        self.assertEqual(result["statuses"], PROJECT_PUBLIC_STATUSES)

    def test_author_match_uses_public_statuses(self):
        applicant = ApplicantFactory()
        # user == author → is_applicant path via author comparison
        result = project_status_bar(DRAFT, user=applicant, author=applicant)
        self.assertEqual(result["statuses"], PROJECT_PUBLIC_STATUSES)

    def test_author_mismatch_uses_user_role(self):
        staff = StaffFactory()
        other = ApplicantFactory()
        # user != author, so is_applicant determined by user.is_applicant (staff → False)
        result = project_status_bar(DRAFT, user=staff, author=other)
        self.assertEqual(result["statuses"], PROJECT_STATUS_CHOICES)

    def test_current_status_index_draft(self):
        staff = StaffFactory()
        result = project_status_bar(DRAFT, staff)
        self.assertEqual(result["current_status_index"], 0)

    def test_current_status_index_internal_approval(self):
        staff = StaffFactory()
        result = project_status_bar(INTERNAL_APPROVAL, staff)
        self.assertEqual(result["current_status_index"], 1)

    def test_current_status_index_contracting(self):
        staff = StaffFactory()
        result = project_status_bar(CONTRACTING, staff)
        self.assertEqual(result["current_status_index"], 2)

    def test_current_status_is_passed_through(self):
        staff = StaffFactory()
        result = project_status_bar(INVOICING_AND_REPORTING, staff)
        self.assertEqual(result["current_status"], INVOICING_AND_REPORTING)

    def test_current_status_name_is_human_readable(self):
        staff = StaffFactory()
        result = project_status_bar(DRAFT, staff)
        self.assertEqual(str(result["current_status_name"]), "Draft")

    def test_css_class_passed_through(self):
        staff = StaffFactory()
        result = project_status_bar(DRAFT, staff, css_class="my-class")
        self.assertEqual(result["class"], "my-class")

    def test_css_class_empty_by_default(self):
        staff = StaffFactory()
        result = project_status_bar(DRAFT, staff)
        self.assertEqual(result["class"], "")
