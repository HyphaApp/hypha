"""Tests for hypha/apply/funds/management/commands/submission_cleanup.py"""

import argparse
import importlib
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.apps import apps
from django.contrib.postgres.search import SearchVectorField
from django.core.management import call_command
from django.db.models import Value
from django.db.models.functions import Cast
from django.test import TestCase
from django.utils import timezone

from hypha.apply.activity.models import Activity
from hypha.apply.activity.options import MESSAGES
from hypha.apply.funds.management.commands.submission_cleanup import (
    check_not_negative_or_zero,
)
from hypha.apply.funds.models import ApplicationRevision
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.funds.workflows.constants import DRAFT_STATE
from hypha.apply.users.tests.factories import StaffFactory


class TestCheckNotNegativeOrZero(TestCase):
    def test_valid_positive_integer(self):
        self.assertEqual(check_not_negative_or_zero("5"), 5)
        self.assertEqual(check_not_negative_or_zero("1"), 1)
        self.assertEqual(check_not_negative_or_zero("100"), 100)

    def test_zero_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            check_not_negative_or_zero("0")

    def test_negative_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            check_not_negative_or_zero("-1")

    def test_non_numeric_raises(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            check_not_negative_or_zero("abc")


class TestSubmissionCleanupCommand(TestCase):
    def _call(self, *args, **kwargs):
        out = StringIO()
        call_command("submission_cleanup", *args, stdout=out, **kwargs)
        return out.getvalue()

    def _make_old_draft(self, days=30):
        """Create a draft submission with a revision timestamp in the past."""
        submission = ApplicationSubmissionFactory(status=DRAFT_STATE)
        old_date = timezone.now() - timedelta(days=days)
        # auto_now=True means we must use update() to set a past timestamp
        ApplicationRevision.objects.filter(id=submission.draft_revision_id).update(
            timestamp=old_date
        )
        return submission

    def _make_old_submission(self, days=30):
        """Create a non-draft submission with an old activity timestamp."""
        submission = ApplicationSubmissionFactory(status="internal_review")
        old_datetime = timezone.now() - timedelta(days=days)
        user = StaffFactory()
        Activity.objects.create(
            source=submission,
            user=user,
            message="old activity",
            timestamp=old_datetime,
            type=MESSAGES.TRANSITION,
        )
        return submission

    def test_no_args_prints_usage_hint(self):
        out = self._call()
        self.assertIn("--drafts", out)

    def test_drafts_no_matching_drafts_skips(self):
        # A recent draft should not be picked up by --drafts 1 (1 day threshold)
        ApplicationSubmissionFactory(status=DRAFT_STATE)
        out = self._call("--drafts", "1", "--noinput")
        self.assertIn("Skipping", out)

    def test_drafts_deletes_old_drafts(self):
        draft = self._make_old_draft(days=30)
        draft_id = draft.id

        out = self._call("--drafts", "1", "--noinput")

        self.assertIn("deleted", out)
        self.assertFalse(ApplicationSubmission.objects.filter(id=draft_id).exists())

    def test_drafts_does_not_delete_recent_drafts(self):
        recent_draft = ApplicationSubmissionFactory(status=DRAFT_STATE)
        old_draft = self._make_old_draft(days=30)

        self._call("--drafts", "20", "--noinput")

        # Recent draft should survive; old draft should be gone
        self.assertTrue(
            ApplicationSubmission.objects.filter(id=recent_draft.id).exists()
        )
        self.assertFalse(ApplicationSubmission.objects.filter(id=old_draft.id).exists())

    def test_submissions_no_matching_submissions_skips(self):
        # A non-draft submission with no activities won't satisfy last_update filter
        ApplicationSubmissionFactory(status="internal_review")
        out = self._call("--submissions", "1", "--noinput")
        self.assertIn("Skipping", out)

    def test_submissions_deletes_old_submissions(self):
        submission = self._make_old_submission(days=30)
        submission_id = submission.id

        out = self._call("--submissions", "1", "--noinput")

        self.assertIn("anonymized", out)
        self.assertFalse(
            ApplicationSubmission.objects.filter(id=submission_id).exists()
        )

    def test_submissions_does_not_delete_recent_submissions(self):
        recent = self._make_old_submission(days=1)
        old = self._make_old_submission(days=60)

        self._call("--submissions", "30", "--noinput")

        self.assertTrue(ApplicationSubmission.objects.filter(id=recent.id).exists())
        self.assertFalse(ApplicationSubmission.objects.filter(id=old.id).exists())

    def test_submissions_excludes_draft_submissions(self):
        draft = self._make_old_draft(days=30)
        draft_id = draft.id
        # Also add an old activity so it would match via last_update if not excluded
        old_datetime = timezone.now() - timedelta(days=30)
        Activity.objects.create(
            source=draft,
            user=StaffFactory(),
            message="old activity",
            timestamp=old_datetime,
            type=MESSAGES.TRANSITION,
        )

        self._call("--submissions", "1", "--noinput")

        # Draft should NOT be deleted by --submissions
        self.assertTrue(ApplicationSubmission.objects.filter(id=draft_id).exists())


class TestRebuildSearchIndex(TestCase):
    def test_rebuilds_search_document(self):
        submission = ApplicationSubmissionFactory(form_data__char="Mycelium network")
        ApplicationSubmission.objects.filter(pk=submission.pk).update(
            search_document=None
        )
        self.assertFalse(ApplicationSubmission.objects.search("mycelium").exists())

        out = StringIO()
        call_command("rebuild_search_index", stdout=out)

        self.assertEqual(
            list(ApplicationSubmission.objects.search("mycelium")), [submission]
        )
        self.assertIn("1 submissions", out.getvalue())

    def _call_with_broken(self, broken_pk, error):
        original = ApplicationSubmission.prepare_search_vector

        def prepare_search_vector(submission):
            if submission.pk == broken_pk:
                return error()
            return original(submission)

        out, err = StringIO(), StringIO()
        with mock.patch.object(
            ApplicationSubmission, "prepare_search_vector", prepare_search_vector
        ):
            call_command("rebuild_search_index", stdout=out, stderr=err)
        return out.getvalue(), err.getvalue()

    def test_reports_and_skips_submission_that_raises(self):
        broken = ApplicationSubmissionFactory()
        submission = ApplicationSubmissionFactory(form_data__char="Mycelium network")
        ApplicationSubmission.objects.update(search_document=None)

        def error():
            raise TypeError("boom")

        out, err = self._call_with_broken(broken.pk, error)

        self.assertEqual(
            list(ApplicationSubmission.objects.search("mycelium")), [submission]
        )
        self.assertIn("1 submissions", out)
        self.assertIn(f"Could not index submission {broken.pk}: boom", err)

    def test_reports_and_skips_submission_rejected_by_database(self):
        broken = ApplicationSubmissionFactory()
        submission = ApplicationSubmissionFactory(form_data__char="Mycelium network")
        ApplicationSubmission.objects.update(search_document=None)

        def error():
            # Not valid tsvector syntax, so Postgres rejects the update.
            return Cast(Value("'unterminated"), SearchVectorField())

        out, err = self._call_with_broken(broken.pk, error)

        self.assertEqual(
            list(ApplicationSubmission.objects.search("mycelium")), [submission]
        )
        self.assertIn("1 submissions", out)
        self.assertIn(f"Could not index submission {broken.pk}", err)

    def test_reports_and_skips_submission_that_cannot_be_loaded(self):
        broken = ApplicationSubmissionFactory()
        submission = ApplicationSubmissionFactory(form_data__char="Mycelium network")
        ApplicationSubmission.objects.update(search_document=None)
        original = ApplicationSubmission.deserialised_data

        def deserialised_data(instance, data, form_fields):
            if instance.pk == broken.pk:
                raise KeyError("removed_block")
            return original(instance, data, form_fields)

        out, err = StringIO(), StringIO()
        with mock.patch.object(
            ApplicationSubmission, "deserialised_data", deserialised_data
        ):
            call_command("rebuild_search_index", stdout=out, stderr=err)

        self.assertEqual(
            list(ApplicationSubmission.objects.search("mycelium")), [submission]
        )
        self.assertIn("Rebuilt search index for 1 submissions", out.getvalue())
        self.assertIn(f"Could not index submission {broken.pk}", err.getvalue())


class TestRemoveSearchDataMigration(TestCase):
    migration = importlib.import_module(
        "hypha.apply.funds.migrations.0140_remove_applicationsubmission_search_data"
    )

    def _rebuild(self):
        self.migration.rebuild_search_index(apps, None)

    def test_new_install_does_not_run_the_command(self):
        with mock.patch.object(self.migration, "call_command") as command:
            self._rebuild()
        command.assert_not_called()

    def test_existing_submissions_run_the_command(self):
        ApplicationSubmissionFactory()
        with mock.patch.object(self.migration, "call_command") as command:
            self._rebuild()
        command.assert_called_once_with("rebuild_search_index")
