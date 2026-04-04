"""Tests for activity/services.py."""

from django.test import TestCase

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import ApplicantFactory, StaffFactory

from ..models import Activity
from ..services import delete_comment, edit_comment, get_comment_count
from .factories import CommentFactory


class TestEditComment(TestCase):
    def test_same_message_returns_original_unchanged(self):
        comment = CommentFactory(message="hello")
        result = edit_comment(comment, "hello")
        self.assertEqual(result.pk, comment.pk)
        self.assertIsNone(result.previous)

    def test_new_message_updates_activity(self):
        comment = CommentFactory(message="old")
        edit_comment(comment, "new")
        comment.refresh_from_db()
        self.assertEqual(comment.message, "new")

    def test_edit_creates_clone_with_current_false(self):
        comment = CommentFactory(message="original")
        pk_before = comment.pk
        edit_comment(comment, "updated")
        # A non-current clone should exist
        clone = Activity.objects.get(pk__gt=pk_before - 1, current=False)
        self.assertFalse(clone.current)
        self.assertEqual(clone.message, "original")

    def test_edited_activity_remains_current(self):
        comment = CommentFactory(message="old")
        result = edit_comment(comment, "new")
        self.assertTrue(result.current)

    def test_edited_activity_has_edited_timestamp(self):
        comment = CommentFactory(message="old")
        result = edit_comment(comment, "new")
        self.assertIsNotNone(result.edited)

    def test_previous_link_set_on_edited_activity(self):
        comment = CommentFactory(message="old")
        result = edit_comment(comment, "new")
        self.assertIsNotNone(result.previous)

    def test_double_edit_creates_chain(self):
        comment = CommentFactory(message="v1")
        edit_comment(comment, "v2")
        edit_comment(comment, "v3")
        comment.refresh_from_db()
        self.assertEqual(comment.message, "v3")
        # Two non-current clones exist
        non_current = Activity.objects.filter(current=False)
        self.assertGreaterEqual(non_current.count(), 2)


class TestDeleteComment(TestCase):
    def test_message_cleared_after_delete(self):
        comment = CommentFactory(message="to delete")
        delete_comment(comment)
        comment.refresh_from_db()
        self.assertEqual(comment.message, "")

    def test_deleted_timestamp_set(self):
        comment = CommentFactory()
        delete_comment(comment)
        comment.refresh_from_db()
        self.assertIsNotNone(comment.deleted)

    def test_edited_timestamp_cleared(self):
        from django.utils import timezone

        comment = CommentFactory()
        comment.edited = timezone.now()
        comment.save()
        delete_comment(comment)
        comment.refresh_from_db()
        self.assertIsNone(comment.edited)

    def test_clone_created_with_current_false(self):
        comment = CommentFactory(message="original text")
        delete_comment(comment)
        clone = Activity.objects.filter(current=False).first()
        self.assertIsNotNone(clone)
        self.assertEqual(clone.message, "original text")

    def test_activity_remains_current_after_delete(self):
        comment = CommentFactory()
        result = delete_comment(comment)
        self.assertTrue(result.current)


class TestGetCommentCount(TestCase):
    def test_count_for_submission_with_no_comments(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory()
        count = get_comment_count(submission, staff)
        self.assertEqual(count, 0)

    def test_count_includes_visible_comments(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory()
        CommentFactory(source=submission, user=staff)
        count = get_comment_count(submission, staff)
        self.assertEqual(count, 1)

    def test_count_excludes_non_current(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory()
        comment = CommentFactory(source=submission, user=staff, message="v1")
        # Editing creates a non-current clone
        edit_comment(comment, "v2")
        count = get_comment_count(submission, staff)
        # Only the current one is counted
        self.assertEqual(count, 1)

    def test_applicant_sees_own_comment(self):
        applicant = ApplicantFactory()
        submission = ApplicationSubmissionFactory(user=applicant)
        CommentFactory(source=submission, user=applicant)
        count = get_comment_count(submission, applicant)
        self.assertGreaterEqual(count, 1)
