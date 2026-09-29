from django.test import TestCase

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory

from ..options import MAYBE, NA, NO, YES
from .factories import ReviewFactory, ReviewOpinionFactory


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


class TestReviewScores(TestCase):
    def test_scores_read_from_answers(self):
        review = ReviewFactory()
        for i, field in enumerate(review.score_fields):
            review.form_data[field.id] = ["", i]
        for i, field in enumerate(review.score_fields_without_text):
            review.form_data[field.id] = i

        scores = review.get_scores(review.form_data)
        self.assertEqual(
            scores,
            list(range(len(review.score_fields)))
            + list(range(len(review.score_fields_without_text))),
        )

    def test_na_answers_score_zero(self):
        review = ReviewFactory()
        field = review.score_fields[0]
        review.form_data[field.id] = ["", NA]
        self.assertEqual(review.get_scores(review.form_data)[0], 0)
