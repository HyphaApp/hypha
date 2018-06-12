from django.test import TestCase
from django.urls import reverse

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory, StaffFactory


class SubmissionTestCase(TestCase):
    user_factory = None

    def setUp(self):
        self.user = self.user_factory()
        self.client.force_login(self.user)

    def get_submission_page(self, submission, view_name='detail'):
        view_name = f'funds:submissions:{ view_name }'
        detail_url = reverse(view_name, kwargs={'pk': submission.id})
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

    def test_can_edit_own_submission(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        submission.status = 'Proposal__invited-for-proposal__0'
        submission.save()
        response = self.get_submission_page(submission, 'edit')
        self.assertContains(response, submission.title)

    def test_cant_edit_submission_incorrect_state(self):
        submission = ApplicationSubmissionFactory(user=self.user, workflow_stages=2)
        response = self.get_submission_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)

    def test_cant_edit_other_submission(self):
        submission = ApplicationSubmissionFactory()
        submission.status='Proposal__invited-for-proposal__0'
        submission.save()
        response = self.get_submission_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)
