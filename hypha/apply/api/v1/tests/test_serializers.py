from django.test import override_settings, TestCase

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.review.tests.factories import ReviewFactory

from ..serializers import ReviewSummarySerializer


@override_settings(ROOT_URLCONF='hypha.apply.urls')
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
