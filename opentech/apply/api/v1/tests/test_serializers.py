from django.test import override_settings, RequestFactory, TestCase

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory, WorkflowVariedApplicationSubmission
from opentech.apply.review.tests.factories import ReviewFactory
from opentech.apply.users.tests.factories import StaffFactory

from ..serializers import ReviewSummarySerializer, ActionSerializer


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestReviewSummarySerializer(TestCase):
    def test_handles_no_reviews(self):
        submission = ApplicationSubmissionFactory()
        data = ReviewSummarySerializer(submission).data
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['score'], None)
        self.assertEqual(data['recommendation'], {'value': -1, 'display': None})
        self.assertEqual(data['assigned'], [])
        self.assertEqual(data['reviews'], [])

    def test_handles_negative_reviews(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(submission=submission)
        data = ReviewSummarySerializer(submission).data
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['score'], 0)
        self.assertEqual(data['recommendation'], {'value': 0, 'display': 'No'})
        self.assertEqual(len(data['assigned']), 1)
        self.assertEqual(len(data['reviews']), 1)


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestActionSerializer(TestCase):
    def setUp(self):
        self.user = StaffFactory()
        request = RequestFactory().get('/')
        request.user = self.user

        self.field = ActionSerializer()
        self.field._context = {'request': request}

    def test_submission_with_no_actions(self):
        submission = WorkflowVariedApplicationSubmission(no_actions=True)
        out = self.field.to_representation(submission)
        self.assertEqual(out, [])

    def test_submission_includes_actions(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        out = self.field.to_representation(submission)
        self.assertEqual(len(out), 5)
        self.assertCountEqual(list(out[0].keys()), ['value', 'type', 'display', 'target'])
