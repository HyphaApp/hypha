from django.urls import reverse

from opentech.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from opentech.apply.utils.testing.tests import BaseViewTestCase

from .factories import ReviewFactory, ReviewFormFieldsFactory, ReviewFormFactory
from ..models import Review
from ..options import NA


class StaffReviewsTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}

    def test_can_access_review(self):
        review = ReviewFactory(author=self.user)
        response = self.get_page(review)
        self.assertContains(response, review.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': review.submission.id}))

    def test_cant_access_other_review(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        response = self.get_page(review)
        self.assertEqual(response.status_code, 403)


class StaffReviewListingTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_review_listing(self):
        submission = ApplicationSubmissionFactory()
        reviews = ReviewFactory.create_batch(3, submission=submission)
        response = self.get_page(submission, 'list')
        self.assertContains(response, submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))
        for review in reviews:
            self.assertContains(response, review.author.full_name)

    def test_draft_reviews_dont_appear(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory.create(submission=submission, is_draft=True)
        response = self.get_page(submission, 'list')
        self.assertContains(response, submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))
        self.assertNotContains(response, review.author.full_name)


class StaffReviewFormTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = ApplicationSubmissionFactory(status='internal_review')

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_form(self):
        response = self.get_page(self.submission, 'form')
        self.assertContains(response, self.submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': self.submission.id}))

    def test_cant_access_wrong_status(self):
        submission = ApplicationSubmissionFactory(rejected=True)
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)

    def test_cant_resubmit_review(self):
        ReviewFactory(submission=self.submission, author=self.user)
        response = self.post_page(self.submission, {'data': 'value'}, 'form')
        self.assertEqual(response.context['has_submitted_review'], True)
        self.assertEqual(response.context['title'], 'Update Review draft')

    def test_can_edit_draft_review(self):
        ReviewFactory(submission=self.submission, author=self.user, is_draft=True)
        response = self.get_page(self.submission, 'form')
        self.assertEqual(response.context['has_submitted_review'], False)
        self.assertEqual(response.context['title'], 'Update Review draft')

    def test_revision_captured_on_review(self):
        form = self.submission.round.review_forms.first()

        data = ReviewFormFieldsFactory.form_response(form.fields)

        self.post_page(self.submission, data, 'form')
        review = self.submission.reviews.first()
        self.assertEqual(review.revision, self.submission.live_revision)

    def test_can_submit_draft_review(self):
        form = self.submission.round.review_forms.first()

        data = ReviewFormFieldsFactory.form_response(form.fields)
        data['save_draft'] = True
        self.post_page(self.submission, data, 'form')
        review = self.submission.reviews.first()
        self.assertTrue(review.is_draft)
        self.assertIsNone(review.revision)


class TestReviewScore(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = ApplicationSubmissionFactory(status='internal_review')

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def submit_review_scores(self, *scores):
        if scores:
            form = ReviewFormFactory(form_fields__multiple__score=len(scores))
        else:
            form = ReviewFormFactory(form_fields__exclude__score=True)
        review_form = self.submission.round.review_forms.first()
        review_form.form = form
        review_form.save()

        data = ReviewFormFieldsFactory.form_response(form.form_fields, {
            field.id: {'score': score}
            for field, score in zip(form.score_fields, scores)
        })

        # Make a new person for every review
        self.client.force_login(self.user_factory())
        response = self.post_page(self.submission, data, 'form')
        self.assertIn(
            'funds/applicationsubmission_admin_detail.html',
            response.template_name,
            msg='Failed to post the form correctly'
        )
        self.client.force_login(self.user)
        return self.submission.reviews.first()

    def test_score_calculated(self):
        review = self.submit_review_scores(5)
        self.assertEqual(review.score, 5)

    def test_average_score_calculated(self):
        review = self.submit_review_scores(1, 5)
        self.assertEqual(review.score, (1 + 5) / 2)

    def test_no_score_is_NA(self):
        review = self.submit_review_scores()
        self.assertEqual(review.score, NA)

    def test_na_not_included_in_review_average(self):
        review = self.submit_review_scores(NA, 5)
        self.assertEqual(review.score, 5)

    def test_na_not_included_reviews_average(self):
        self.submit_review_scores(NA)
        self.assertIsNone(Review.objects.score())

    def test_na_not_included_multiple_reviews_average(self):
        self.submit_review_scores(NA)
        self.submit_review_scores(5)

        self.assertEqual(Review.objects.count(), 2)
        self.assertEqual(Review.objects.score(), 5)


class UserReviewFormTestCase(BaseViewTestCase):
    user_factory = UserFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_cant_access_form(self):
        submission = ApplicationSubmissionFactory(status='internal_review')
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)


class ReviewDetailTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}

    def test_review_detail_recommendation(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2)
        review = ReviewFactory(submission=submission, author=self.user, recommendation_yes=True)
        response = self.get_page(review)
        self.assertContains(response, submission.title)
        self.assertContains(response, "<p>Yes</p>")
