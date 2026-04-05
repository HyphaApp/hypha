"""Tests for funds/permissions.py."""

from django.test import TestCase, override_settings
from rolepermissions.checkers import has_object_permission

from hypha.apply.funds.models.co_applicants import (
    CoApplicant,
    CoApplicantInvite,
    CoApplicantInviteStatus,
    CoApplicantRole,
)
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.funds.workflows import DRAFT_STATE
from hypha.apply.users.tests.factories import (
    AdminFactory,
    ApplicantFactory,
    ReviewerFactory,
    StaffFactory,
    UserFactory,
)

from ..permissions import (
    can_access_drafts,
    can_alter_archived_submissions,
    can_bulk_archive_submissions,
    can_bulk_delete_submissions,
    can_bulk_update_submissions,
    can_change_external_reviewers,
    can_export_submissions,
    can_invite_co_applicants,
    can_take_submission_actions,
    can_update_co_applicant,
    can_view_archived_submissions,
    can_view_submission,
    get_archive_alter_groups,
    get_archive_view_groups,
    user_can_view_post_comment_form,
)


class TestCanTakeSubmissionActions(TestCase):
    def test_unauthenticated_user_cannot_act(self):
        from django.contrib.auth.models import AnonymousUser

        submission = ApplicationSubmissionFactory()
        result, reason = can_take_submission_actions(AnonymousUser(), submission)
        self.assertFalse(result)

    def test_archived_submission_blocks_actions(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory(is_archive=True)
        result, _ = can_take_submission_actions(staff, submission)
        self.assertFalse(result)

    def test_active_submission_allows_actions(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory()
        result, _ = can_take_submission_actions(staff, submission)
        self.assertTrue(result)


class TestCanBulkOperations(TestCase):
    def test_staff_can_bulk_delete(self):
        self.assertTrue(can_bulk_delete_submissions(StaffFactory()))

    def test_non_staff_cannot_bulk_delete(self):
        self.assertFalse(can_bulk_delete_submissions(ApplicantFactory()))

    def test_staff_can_bulk_update(self):
        self.assertTrue(can_bulk_update_submissions(StaffFactory()))

    def test_non_staff_cannot_bulk_update(self):
        self.assertFalse(can_bulk_update_submissions(ReviewerFactory()))


class TestCanViewArchivedSubmissions(TestCase):
    @override_settings(
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF=True,
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_can_view_archived_when_setting_enabled(self):
        self.assertTrue(can_view_archived_submissions(StaffFactory()))

    @override_settings(
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF=False,
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_cannot_view_archived_when_setting_disabled(self):
        self.assertFalse(can_view_archived_submissions(StaffFactory()))

    def test_applicant_cannot_view_archived(self):
        self.assertFalse(can_view_archived_submissions(ApplicantFactory()))


class TestCanAlterArchivedSubmissions(TestCase):
    @override_settings(
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF=True,
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_can_alter_when_setting_enabled(self):
        result, _ = can_alter_archived_submissions(StaffFactory())
        self.assertTrue(result)

    @override_settings(
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF=False,
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_cannot_alter_when_setting_disabled(self):
        result, _ = can_alter_archived_submissions(StaffFactory())
        self.assertFalse(result)

    def test_applicant_cannot_alter(self):
        result, _ = can_alter_archived_submissions(ApplicantFactory())
        self.assertFalse(result)


class TestCanBulkArchive(TestCase):
    @override_settings(
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF=True,
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF=True,
    )
    def test_staff_can_bulk_archive_with_settings_enabled(self):
        self.assertTrue(can_bulk_archive_submissions(StaffFactory()))

    def test_applicant_cannot_bulk_archive(self):
        self.assertFalse(can_bulk_archive_submissions(ApplicantFactory()))


class TestCanChangeExternalReviewers(TestCase):
    def _ext_review_submission(self, **kwargs):
        # external_review status puts submission in Proposal stage (has_external_review=True)
        return ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, **kwargs
        )

    def test_superuser_can_always_change(self):
        user = UserFactory(is_superuser=True)
        submission = self._ext_review_submission()
        self.assertTrue(can_change_external_reviewers(user, submission))

    def test_lead_can_change_reviewers(self):
        staff = StaffFactory()
        submission = self._ext_review_submission(lead=staff)
        self.assertTrue(can_change_external_reviewers(staff, submission))

    @override_settings(GIVE_STAFF_LEAD_PERMS=True)
    def test_staff_can_change_when_give_staff_lead_perms_enabled(self):
        staff = StaffFactory()
        submission = self._ext_review_submission()
        self.assertTrue(can_change_external_reviewers(staff, submission))

    @override_settings(GIVE_STAFF_LEAD_PERMS=False)
    def test_staff_cannot_change_when_not_lead_and_perms_disabled(self):
        staff = StaffFactory()
        other_staff = StaffFactory()
        submission = self._ext_review_submission(lead=other_staff)
        self.assertFalse(can_change_external_reviewers(staff, submission))

    def test_stage_without_external_review_returns_false(self):
        staff = StaffFactory()
        # Default 1-stage workflow → Request stage → has_external_review=False
        submission = ApplicationSubmissionFactory(workflow_stages=1)
        self.assertFalse(can_change_external_reviewers(staff, submission))


class TestCanAccessDrafts(TestCase):
    @override_settings(
        SUBMISSIONS_DRAFT_ACCESS_STAFF=True,
        SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_can_access_drafts_when_enabled(self):
        self.assertTrue(can_access_drafts(StaffFactory()))

    @override_settings(
        SUBMISSIONS_DRAFT_ACCESS_STAFF=False,
        SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_cannot_access_drafts_when_disabled(self):
        self.assertFalse(can_access_drafts(StaffFactory()))

    def test_applicant_cannot_access_drafts(self):
        self.assertFalse(can_access_drafts(ApplicantFactory()))


class TestCanExportSubmissions(TestCase):
    @override_settings(
        SUBMISSIONS_EXPORT_ACCESS_STAFF=True,
        SUBMISSIONS_EXPORT_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_can_export_when_enabled(self):
        self.assertTrue(can_export_submissions(StaffFactory()))

    @override_settings(
        SUBMISSIONS_EXPORT_ACCESS_STAFF=False,
        SUBMISSIONS_EXPORT_ACCESS_STAFF_ADMIN=False,
    )
    def test_staff_cannot_export_when_disabled(self):
        self.assertFalse(can_export_submissions(StaffFactory()))

    def test_applicant_cannot_export(self):
        self.assertFalse(can_export_submissions(ApplicantFactory()))


class TestIsUserHasAccessToViewSubmission(TestCase):
    def test_unauthenticated_cannot_view(self):
        from django.contrib.auth.models import AnonymousUser

        submission = ApplicationSubmissionFactory()
        result, _ = can_view_submission(AnonymousUser(), submission)
        self.assertFalse(result)

    def test_staff_can_view(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory()
        result, _ = can_view_submission(staff, submission)
        self.assertTrue(result)

    def test_submission_owner_can_view(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        result, _ = can_view_submission(applicant, submission)
        self.assertTrue(result)

    def test_reviewer_can_view(self):
        reviewer = ReviewerFactory()
        submission = ApplicationSubmissionFactory()
        result, _ = can_view_submission(reviewer, submission)
        self.assertTrue(result)

    def test_unrelated_user_cannot_view(self):
        user = UserFactory()
        submission = ApplicationSubmissionFactory()
        result, _ = can_view_submission(user, submission)
        self.assertFalse(result)

    @override_settings(SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF=False)
    def test_staff_cannot_view_archived_when_setting_disabled(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory(is_archive=True)
        result, _ = can_view_submission(staff, submission)
        self.assertFalse(result)


class TestCanInviteCoApplicants(TestCase):
    def test_owner_applicant_can_invite(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        result, _ = can_invite_co_applicants(applicant, submission)
        self.assertTrue(result)

    def test_staff_can_invite(self):
        staff = StaffFactory()
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        result, _ = can_invite_co_applicants(staff, submission)
        self.assertTrue(result)

    def test_unrelated_applicant_cannot_invite(self):
        applicant = ApplicantFactory()
        other = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        result, _ = can_invite_co_applicants(other, submission)
        self.assertFalse(result)

    def test_archived_submission_blocks_invite(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant, is_archive=True)
        result, _ = can_invite_co_applicants(applicant, submission)
        self.assertFalse(result)

    @override_settings(SUBMISSIONS_COAPPLICANT_INVITES_LIMIT=0)
    def test_limit_reached_blocks_invite(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        result, _ = can_invite_co_applicants(applicant, submission)
        self.assertFalse(result)


class TestGetArchiveGroups(TestCase):
    @override_settings(
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF=True,
        SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF_ADMIN=True,
    )
    def test_view_groups_includes_staff_when_enabled(self):
        groups = get_archive_view_groups()
        from hypha.apply.users.roles import STAFF_GROUP_NAME, TEAMADMIN_GROUP_NAME

        self.assertIn(STAFF_GROUP_NAME, groups)
        self.assertIn(TEAMADMIN_GROUP_NAME, groups)

    @override_settings(
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF=True,
        SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN=False,
    )
    def test_alter_groups_includes_staff_when_enabled(self):
        groups = get_archive_alter_groups()
        from hypha.apply.users.roles import STAFF_GROUP_NAME

        self.assertIn(STAFF_GROUP_NAME, groups)


# ---------------------------------------------------------------------------
# Data isolation — cross-user submission access
# ---------------------------------------------------------------------------


class TestCrossUserSubmissionAccess(TestCase):
    """Verify users cannot access each other's submissions via can_view_submission."""

    def test_unrelated_applicant_cannot_view_another_applicants_submission(self):
        owner = ApplicantFactory()
        intruder = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=owner)
        result, _ = can_view_submission(intruder, submission)
        self.assertFalse(result)

    def test_co_applicant_of_one_submission_cannot_view_a_different_submission(self):
        owner = ApplicantFactory()
        co_user = ApplicantFactory()
        submission_a = ApplicationSubmissionFactory(user=owner)
        submission_b = ApplicationSubmissionFactory()

        invite = CoApplicantInvite.objects.create(
            submission=submission_a,
            invited_user_email=co_user.email,
            status=CoApplicantInviteStatus.ACCEPTED,
            role=CoApplicantRole.EDIT,
        )
        CoApplicant.objects.create(
            submission=submission_a,
            user=co_user,
            invite=invite,
            role=CoApplicantRole.EDIT,
        )

        result_a, _ = can_view_submission(co_user, submission_a)
        self.assertTrue(result_a)

        result_b, _ = can_view_submission(co_user, submission_b)
        self.assertFalse(result_b)


# ---------------------------------------------------------------------------
# delete_submission
# ---------------------------------------------------------------------------


class TestDeleteSubmission(TestCase):
    def _can_delete(self, user, submission):
        return has_object_permission("delete_submission", user, obj=submission)

    def test_owner_can_delete_own_draft(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant, status=DRAFT_STATE)
        self.assertTrue(self._can_delete(applicant, submission))

    def test_owner_cannot_delete_own_non_draft_submission(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(
            user=applicant, status="internal_review"
        )
        self.assertFalse(self._can_delete(applicant, submission))

    def test_applicant_cannot_delete_another_users_draft(self):
        owner = ApplicantFactory()
        intruder = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=owner, status=DRAFT_STATE)
        self.assertFalse(self._can_delete(intruder, submission))

    def test_superuser_can_delete_any_submission(self):
        admin = AdminFactory()
        submission = ApplicationSubmissionFactory(status="internal_review")
        self.assertTrue(self._can_delete(admin, submission))


# ---------------------------------------------------------------------------
# can_update_co_applicant — VIEW vs EDIT role distinction
# ---------------------------------------------------------------------------


class TestCanUpdateCoApplicant(TestCase):
    def _make_invite(self, submission, invited_by=None, role=CoApplicantRole.VIEW):
        co_user = ApplicantFactory()
        invite = CoApplicantInvite.objects.create(
            submission=submission,
            invited_user_email=co_user.email,
            invited_by=invited_by,
            status=CoApplicantInviteStatus.ACCEPTED,
            role=role,
        )
        return invite

    def setUp(self):
        self.inviter = ApplicantFactory()
        self.submission = ApplicationSubmissionFactory(user=self.inviter)

    def test_inviter_can_update_their_co_applicant(self):
        invite = self._make_invite(self.submission, invited_by=self.inviter)
        result, _ = can_update_co_applicant(self.inviter, invite)
        self.assertTrue(result)

    def test_submission_owner_can_update_co_applicant(self):
        invite = self._make_invite(self.submission)
        result, _ = can_update_co_applicant(self.inviter, invite)
        self.assertTrue(result)

    def test_staff_can_update_any_co_applicant(self):
        invite = self._make_invite(self.submission)
        result, _ = can_update_co_applicant(StaffFactory(), invite)
        self.assertTrue(result)

    def test_unrelated_applicant_cannot_update_co_applicant(self):
        invite = self._make_invite(self.submission)
        result, _ = can_update_co_applicant(ApplicantFactory(), invite)
        self.assertFalse(result)

    def test_archived_submission_blocks_update(self):
        archived_submission = ApplicationSubmissionFactory(
            user=self.inviter, is_archive=True
        )
        invite = self._make_invite(archived_submission, invited_by=self.inviter)
        result, _ = can_update_co_applicant(self.inviter, invite)
        self.assertFalse(result)


# ---------------------------------------------------------------------------
# user_can_view_post_comment_form — co-applicant VIEW vs EDIT/COMMENT role
# ---------------------------------------------------------------------------


class TestUserCanViewPostCommentForm(TestCase):
    def _make_co_applicant(self, submission, role):
        co_user = ApplicantFactory()
        invite = CoApplicantInvite.objects.create(
            submission=submission,
            invited_user_email=co_user.email,
            status=CoApplicantInviteStatus.ACCEPTED,
            role=role,
        )
        CoApplicant.objects.create(
            submission=submission,
            user=co_user,
            invite=invite,
            role=role,
        )
        return co_user

    def setUp(self):
        self.submission = ApplicationSubmissionFactory()

    def test_view_role_co_applicant_cannot_post_comment(self):
        co_user = self._make_co_applicant(self.submission, CoApplicantRole.VIEW)
        self.assertFalse(user_can_view_post_comment_form(co_user, self.submission))

    def test_edit_role_co_applicant_can_post_comment(self):
        co_user = self._make_co_applicant(self.submission, CoApplicantRole.EDIT)
        self.assertTrue(user_can_view_post_comment_form(co_user, self.submission))

    def test_comment_role_co_applicant_can_post_comment(self):
        co_user = self._make_co_applicant(self.submission, CoApplicantRole.COMMENT)
        self.assertTrue(user_can_view_post_comment_form(co_user, self.submission))

    def test_non_co_applicant_can_post_comment(self):
        self.assertTrue(
            user_can_view_post_comment_form(ApplicantFactory(), self.submission)
        )

    def test_staff_can_post_comment(self):
        self.assertTrue(
            user_can_view_post_comment_form(StaffFactory(), self.submission)
        )
