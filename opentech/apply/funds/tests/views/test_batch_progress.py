from unittest import mock

from opentech.apply.funds.models import ApplicationSubmission

from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    InvitedToProposalFactory,
)
from opentech.apply.users.tests.factories import (
    ReviewerFactory,
    StaffFactory,
    UserFactory,
)
from opentech.apply.utils.testing.tests import BaseViewTestCase


class BaseBatchProgressViewTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:{}'
    base_view_name = 'list'

    def data(self, action, submissions):
        return {
            'form-submitted-batch_progress_form': 'Update',
            'action': action,
            'submissions': ','.join([str(submission.id) for submission in submissions]),
        }


class StaffTestCase(BaseBatchProgressViewTestCase):
    user_factory = StaffFactory

    def test_can_progress_application(self):
        submission = ApplicationSubmissionFactory()
        action = 'open-review'
        self.post_page(data=self.data(action, [submission]))
        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'internal_review')

    def test_can_progress_multiple_applications(self):
        submissions = ApplicationSubmissionFactory.create_batch(3)
        action = 'open-review'
        self.post_page(data=self.data(action, submissions))

        self.assertCountEqual(
            [self.refresh(submission).status for submission in submissions],
            ['internal_review'] * 3,
        )

    def test_cant_progress_in_incorrect_state(self):
        submission = ApplicationSubmissionFactory()
        action = 'close-review'
        self.post_page(data=self.data(action, [submission]))
        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'in_discussion')

    def test_can_progress_one_in_mixed_state(self):
        bad_submission = ApplicationSubmissionFactory()
        good_submission = ApplicationSubmissionFactory(status='internal_review')
        action = 'close-review'
        self.post_page(data=self.data(action, [good_submission, bad_submission]))
        good_submission = self.refresh(good_submission)
        bad_submission = self.refresh(bad_submission)
        self.assertEqual(bad_submission.status, 'in_discussion')
        self.assertEqual(good_submission.status, 'post_review_discussion')

    def test_can_progress_different_states(self):
        submission = ApplicationSubmissionFactory()
        other_submission = InvitedToProposalFactory()
        action = 'open-review'
        self.post_page(data=self.data(action, [submission, other_submission]))
        submission = self.refresh(submission)
        other_submission = self.refresh(other_submission)
        self.assertEqual(submission.status, 'internal_review')
        self.assertEqual(other_submission.status, 'proposal_internal_review')

    @mock.patch('opentech.apply.funds.views.messenger')
    def test_messenger_not_called_with_failed(self, patched):
        submission = ApplicationSubmissionFactory()
        action = 'close-review'
        self.post_page(data=self.data(action, [submission]))
        patched.assert_called_once()
        _, _, kwargs = patched.mock_calls[0]
        self.assertQuerysetEqual(kwargs['submissions'], ApplicationSubmission.objects.none())

    @mock.patch('opentech.apply.funds.views.messenger')
    def test_messenger_with_submission_in_review(self, patched):
        submission = ApplicationSubmissionFactory()
        action = 'open-review'
        self.post_page(data=self.data(action, [submission]))
        self.assertEqual(patched.call_count, 2)
        _, _, kwargs = patched.mock_calls[0]
        self.assertCountEqual(kwargs['submissions'], [submission])
        _, _, kwargs = patched.mock_calls[1]
        self.assertCountEqual(kwargs['submissions'], [submission])


class ReivewersTestCase(BaseBatchProgressViewTestCase):
    user_factory = ReviewerFactory

    def test_cant_post_to_page(self):
        response = self.post_page()
        self.assertEqual(response.status_code, 405)


class ApplicantTestCase(BaseBatchProgressViewTestCase):
    user_factory = UserFactory

    def test_cant_access_page_to_page(self):
        response = self.post_page()
        self.assertEqual(response.status_code, 403)
