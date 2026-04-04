"""Tests for dashboard/services.py."""

from django.test import TestCase

from hypha.apply.projects.tests.factories import (
    PAFApprovalsFactory,
    PAFReviewerRoleFactory,
    ProjectFactory,
)
from hypha.apply.users.tests.factories import StaffFactory

from ..services import get_paf_for_review


class TestGetPafForReview(TestCase):
    def test_returns_unapproved_paf_matching_user_groups(self):
        staff = StaffFactory()
        role = PAFReviewerRoleFactory()
        # Give user exactly the groups the role requires
        staff.groups.set(role.user_roles.all())
        project = ProjectFactory()
        paf = PAFApprovalsFactory(
            project=project, paf_reviewer_role=role, approved=False
        )

        result = get_paf_for_review(user=staff, is_paf_approval_sequential=False)

        self.assertIn(paf, result)

    def test_excludes_already_approved_pafs(self):
        staff = StaffFactory()
        role = PAFReviewerRoleFactory()
        staff.groups.set(role.user_roles.all())
        project = ProjectFactory()
        PAFApprovalsFactory(project=project, paf_reviewer_role=role, approved=True)

        result = get_paf_for_review(user=staff, is_paf_approval_sequential=False)

        self.assertEqual(result.count(), 0)

    def test_excludes_pafs_for_different_role_groups(self):
        staff = StaffFactory()
        # User has no groups matching the role's user_roles
        role = PAFReviewerRoleFactory()
        staff.groups.clear()
        project = ProjectFactory()
        PAFApprovalsFactory(project=project, paf_reviewer_role=role, approved=False)

        result = get_paf_for_review(user=staff, is_paf_approval_sequential=False)

        self.assertEqual(result.count(), 0)

    def test_sequential_excludes_paf_with_earlier_unapproved_role(self):
        staff = StaffFactory()
        role1 = PAFReviewerRoleFactory()
        role2 = PAFReviewerRoleFactory()
        # Ensure role1 sort_order < role2 sort_order
        role1.sort_order = 0
        role1.save()
        role2.sort_order = 1
        role2.save()

        staff.groups.set(role2.user_roles.all())
        project = ProjectFactory()
        # role1 unapproved (lower order) — blocks role2
        PAFApprovalsFactory(project=project, paf_reviewer_role=role1, approved=False)
        paf2 = PAFApprovalsFactory(
            project=project, paf_reviewer_role=role2, approved=False
        )

        result = get_paf_for_review(user=staff, is_paf_approval_sequential=True)

        self.assertNotIn(paf2, result)

    def test_sequential_includes_paf_when_earlier_role_is_approved(self):
        staff = StaffFactory()
        role1 = PAFReviewerRoleFactory()
        role2 = PAFReviewerRoleFactory()
        role1.sort_order = 0
        role1.save()
        role2.sort_order = 1
        role2.save()

        staff.groups.set(role2.user_roles.all())
        project = ProjectFactory()
        # role1 already approved — role2 can proceed
        PAFApprovalsFactory(project=project, paf_reviewer_role=role1, approved=True)
        paf2 = PAFApprovalsFactory(
            project=project, paf_reviewer_role=role2, approved=False
        )

        result = get_paf_for_review(user=staff, is_paf_approval_sequential=True)

        self.assertIn(paf2, result)

    def test_non_sequential_includes_paf_even_with_earlier_unapproved_role(self):
        staff = StaffFactory()
        role1 = PAFReviewerRoleFactory()
        role2 = PAFReviewerRoleFactory()
        role1.sort_order = 0
        role1.save()
        role2.sort_order = 1
        role2.save()

        staff.groups.set(role2.user_roles.all())
        project = ProjectFactory()
        PAFApprovalsFactory(project=project, paf_reviewer_role=role1, approved=False)
        paf2 = PAFApprovalsFactory(
            project=project, paf_reviewer_role=role2, approved=False
        )

        result = get_paf_for_review(user=staff, is_paf_approval_sequential=False)

        self.assertIn(paf2, result)

    def test_returns_empty_queryset_when_no_pafs(self):
        staff = StaffFactory()
        result = get_paf_for_review(user=staff, is_paf_approval_sequential=False)
        self.assertEqual(result.count(), 0)
