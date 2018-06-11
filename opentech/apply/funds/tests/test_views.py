from django.test import TestCase
from django.urls import reverse

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory, StaffFactory


class SubmissionTestCase(TestCase):
    user_factory = None

    def setUp(self):
        self.user = self.user_factory()
        self.client.force_login(self.user)

    def get_submission_page(self, submission):
        detail_url = reverse('funds:submission', kwargs={'pk': submission.id})
        return self.client.get(detail_url)


class TestStaffSubmissionView(SubmissionTestCase):
    user_factory = StaffFactory

    def test_can_view_a_submission(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_submission_page(submission)
        self.assertContains(response, submission.title)


class TestApplicantSubmissionView(SubmissionTestCase):
    user_factory = UserFactory

    def test_can_view_own_submission(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        response = self.get_submission_page(submission)
        self.assertContains(response, submission.title)

    def test_cant_view_others_submission(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_submission_page(submission)
        self.assertEqual(response.status_code, 403)
