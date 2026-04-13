from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from hypha.apply.activity.models import Event
from hypha.apply.activity.options import MESSAGES
from hypha.apply.funds.models.submissions import (
    AnonymizedSubmission,
    ApplicationSubmission,
)
from hypha.apply.funds.services import bulk_anonymize_submissions
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.funds.workflows.constants import DRAFT_STATE
from hypha.apply.users.tests.factories import StaffFactory


class BulkActions(TestCase):
    def dummy_request(self, path):
        request = RequestFactory().get(path)
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = StaffFactory()
        request._messages = FallbackStorage(request)
        return request

    def test_bulk_anonymize_submissions(self):
        self.maxDiff = None
        request = self.dummy_request("/apply/submissions/all/bulk_anonymize/")
        user = StaffFactory()
        submissions = ApplicationSubmissionFactory.create_batch(4)
        submission_values = [
            {
                "id": submission.id,
                "value": submission.form_data["value"],
                "page": submission.page.id,
                "status": submission.status,
                "round": submission.round.id,
                "submit_time": submission.submit_time,
                "screening_status": submission.get_current_screening_status(),
            }
            for submission in submissions
        ]
        submission_qs = ApplicationSubmission.objects.filter(
            id__in=[submission["id"] for submission in submission_values]
        )

        anonymized = bulk_anonymize_submissions(submission_qs, user, request)
        self.assertEqual(len(submission_values), len(anonymized))

    def test_bulk_anonymize_deletes_original_submissions(self):
        request = self.dummy_request("/apply/submissions/all/bulk_anonymize/")
        user = StaffFactory()
        submissions = ApplicationSubmissionFactory.create_batch(3)
        ids = [s.id for s in submissions]
        submission_qs = ApplicationSubmission.objects.filter(id__in=ids)

        bulk_anonymize_submissions(submission_qs, user, request)

        self.assertEqual(ApplicationSubmission.objects.filter(id__in=ids).count(), 0)

    def test_bulk_anonymize_preserves_field_values(self):
        request = self.dummy_request("/apply/submissions/all/bulk_anonymize/")
        user = StaffFactory()
        submission = ApplicationSubmissionFactory()
        expected_value = submission.form_data["value"]
        expected_page = submission.page.id
        expected_round = submission.round.id
        expected_status = submission.status

        submission_qs = ApplicationSubmission.objects.filter(id=submission.id)
        anonymized = bulk_anonymize_submissions(submission_qs, user, request)

        self.assertEqual(len(anonymized), 1)
        anon = anonymized[0]
        self.assertEqual(anon.value, expected_value)
        self.assertEqual(anon.page.id, expected_page)
        self.assertEqual(anon.round.id, expected_round)
        self.assertEqual(anon.status, expected_status)

    def test_bulk_anonymize_excludes_draft_submissions(self):
        request = self.dummy_request("/apply/submissions/all/bulk_anonymize/")
        user = StaffFactory()
        draft = ApplicationSubmissionFactory(status=DRAFT_STATE)
        non_draft = ApplicationSubmissionFactory()
        ids = [draft.id, non_draft.id]
        submission_qs = ApplicationSubmission.objects.filter(id__in=ids)

        anonymized = bulk_anonymize_submissions(submission_qs, user, request)

        # Only the non-draft should be in the anonymized list
        self.assertEqual(len(anonymized), 1)
        self.assertEqual(AnonymizedSubmission.objects.count(), 1)

    def test_bulk_anonymize_deletes_new_submission_events(self):
        request = self.dummy_request("/apply/submissions/all/bulk_anonymize/")
        user = StaffFactory()
        submission = ApplicationSubmissionFactory()
        Event.objects.create(
            type=MESSAGES.NEW_SUBMISSION,
            object_id=submission.id,
            by=user,
        )
        submission_qs = ApplicationSubmission.objects.filter(id=submission.id)

        bulk_anonymize_submissions(submission_qs, user, request)

        remaining = Event.objects.filter(
            type=MESSAGES.NEW_SUBMISSION, object_id=submission.id
        )
        self.assertEqual(remaining.count(), 0)
