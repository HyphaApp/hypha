from django.test import TestCase, RequestFactory
from django.urls import reverse

from opentech.apply.users.tests.factories import StaffFactory
from .factories import ReviewFactory
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory


class BaseTestCase(TestCase):
    url_name = ''
    user_factory = None

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.user_factory()
        self.client.force_login(self.user)

    def url(self, instance, view_name='review'):
        full_url_name = self.url_name.format(view_name)
        url = reverse(full_url_name, kwargs=self.get_kwargs(instance))
        request = self.factory.get(url, secure=True)
        return request.build_absolute_uri()

    def get_page(self, instance, view_name='review'):
        return self.client.get(self.url(instance, view_name), secure=True, follow=True)

    def post_page(self, instance, data, view_name='review'):
        return self.client.post(self.url(instance, view_name), data, secure=True, follow=True)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)


class StaffReviewsTestCase(BaseTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'

    def get_kwargs(self, instance):
        return {'pk': instance.id, 'submission_pk': instance.submission.id}

    def test_can_access_review(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission, author=self.user)
        response = self.get_page(review)
        self.assertContains(response, review.submission.title)
        self.assertContains(response, self.user.full_name)

    def test_cant_access_other_review(self):
        submission = ApplicationSubmissionFactory()
        review = ReviewFactory(submission=submission)
        response = self.get_page(review)
        self.assertEqual(response.status_code, 403)


class StaffReviewListingTestCase(BaseTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:reviews:{}'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_review_listing(self):
        submission = ApplicationSubmissionFactory()
        reviews = ReviewFactory.create_batch(3, submission=submission)
        response = self.get_page(submission, 'list')
        self.assertContains(response, submission.title)
        for review in reviews:
            self.assertContains(response, review.author.full_name)
