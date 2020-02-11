from django.test import TestCase

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from .factories import ReviewFactory, ReviewOpinionFactory
from ..options import MAYBE, NO, YES


class TestReviewQueryset(TestCase):
    def test_reviews_yes(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(recommendation_yes=True, submission=submission)
        ReviewFactory(recommendation_yes=True, submission=submission)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, YES)

    def test_reviews_no(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(submission=submission)
        ReviewFactory(submission=submission)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, NO)

    def test_reviews_maybe(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(recommendation_maybe=True, submission=submission)
        ReviewFactory(recommendation_maybe=True, submission=submission)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, MAYBE)

    def test_reviews_mixed(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(recommendation_yes=True, submission=submission)
        ReviewFactory(submission=submission)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, MAYBE)

    def test_review_yes_opinion_agree(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(recommendation_yes=True, submission=submission)
        ReviewOpinionFactory(review=review, opinion_agree=True)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, YES)

    def test_review_yes_opinion_disagree(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(recommendation_yes=True, submission=submission)
        ReviewOpinionFactory(review=review, opinion_disagree=True)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, MAYBE)

    def test_review_no_opinion_agree(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        ReviewOpinionFactory(review=review, opinion_agree=True)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, NO)

    def test_review_no_opinion_disagree(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        ReviewOpinionFactory(review=review, opinion_disagree=True)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, MAYBE)

    def test_review_not_all_opinion(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(recommendation_yes=True, submission=submission)
        review = ReviewFactory(recommendation_yes=True, submission=submission)
        ReviewOpinionFactory(review=review, opinion_agree=True)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, YES)

    def test_review_yes_mixed_opinion(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        ReviewOpinionFactory(review=review, opinion_agree=True)
        ReviewOpinionFactory(review=review, opinion_disagree=True)
        recommendation = submission.reviews.recommendation()
        self.assertEqual(recommendation, MAYBE)
