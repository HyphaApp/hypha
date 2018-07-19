from django.urls import reverse

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from opentech.apply.utils.tests import BaseViewTestCase
from .factories.models import ReviewFactory


class StaffReviewsTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}

    def test_can_access_review(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission, author=self.user)
        response = self.get_page(review)
        self.assertContains(response, review.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))

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


class StaffReviewFormTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'
    base_view_name = 'review'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_form(self):
        submission = ApplicationSubmissionFactory(status='internal_review')
        response = self.get_page(submission, 'form')
        self.assertContains(response, submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))

    def test_cant_access_wrong_status(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)

    def test_cant_resubmit_review(self):
        submission = ApplicationSubmissionFactory(status='internal_review')
        ReviewFactory(submission=submission, author=self.user)
        response = self.post_page(submission, {'data': 'value'}, 'form')
        self.assertEqual(response.context['has_submitted_review'], True)
        self.assertEqual(response.context['title'], 'Update Review draft')

    def test_can_edit_draft_review(self):
        submission = ApplicationSubmissionFactory(status='internal_review')
        ReviewFactory(submission=submission, author=self.user, is_draft=True)
        response = self.post_page(submission, {'data': 'value'}, 'form')
        self.assertEqual(response.context['has_submitted_review'], False)
        self.assertEqual(response.context['title'], 'Update Review draft')


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

    def test_review_detail_field_groups(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2)
        review = ReviewFactory(submission=submission, author=self.user)
        response = self.get_page(review)
        self.assertContains(response, submission.title)
        self.assertContains(response, "<h4>A. Conflicts of Interest and Confidentiality</h4>")
