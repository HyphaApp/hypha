from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.services import bulk_covert_to_skeleton_submissions
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
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

    def test_bulk_skeleton_submissions(self):
        self.maxDiff = None
        request = self.dummy_request("/apply/submissions/all/bulk_skeleton/")
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

        skeletons = bulk_covert_to_skeleton_submissions(submission_qs, user, request)
        self.assertEqual(len(submission_values), len(skeletons))
