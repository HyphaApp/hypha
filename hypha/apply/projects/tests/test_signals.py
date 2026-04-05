"""Tests for projects/signals.py."""

from django.test import TestCase

from ..models.project import DRAFT, INTERNAL_APPROVAL
from .factories import PAFApprovalsFactory, PAFReviewerRoleFactory, ProjectFactory


class TestHandleInternalApprovalProjectsSignal(TestCase):
    def test_deleting_last_paf_role_reverts_internal_approval_projects_to_draft(self):
        role = PAFReviewerRoleFactory()
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        PAFApprovalsFactory(project=project, paf_reviewer_role=role)

        self.assertEqual(project.paf_approvals.count(), 1)

        role.delete()

        project.refresh_from_db()
        self.assertEqual(project.status, DRAFT)

    def test_deleting_last_paf_role_removes_paf_approvals(self):
        role = PAFReviewerRoleFactory()
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        PAFApprovalsFactory(project=project, paf_reviewer_role=role)

        role.delete()

        self.assertEqual(project.paf_approvals.count(), 0)

    def test_deleting_non_last_paf_role_does_not_affect_projects(self):
        role1 = PAFReviewerRoleFactory()
        role2 = PAFReviewerRoleFactory()  # noqa: F841 — keeps count > 0 after role1 deletion
        project = ProjectFactory(status=INTERNAL_APPROVAL)
        PAFApprovalsFactory(project=project, paf_reviewer_role=role1)

        role1.delete()

        project.refresh_from_db()
        # role2 still exists, so signal should not revert the project
        self.assertEqual(project.status, INTERNAL_APPROVAL)

    def test_deleting_paf_role_only_affects_internal_approval_projects(self):
        role = PAFReviewerRoleFactory()
        contracting_project = ProjectFactory(status="contracting")

        role.delete()

        contracting_project.refresh_from_db()
        self.assertEqual(contracting_project.status, "contracting")
