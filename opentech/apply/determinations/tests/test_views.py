from django.urls import reverse

from opentech.apply.activity.models import Activity
from opentech.apply.determinations.models import ACCEPTED
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.utils.testing import BaseViewTestCase

from .factories import DeterminationFactory


class StaffDeterminationsTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:determinations:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.submission.id}

    def test_can_access_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        determination = DeterminationFactory(submission=submission, author=self.user, not_draft=True)
        response = self.get_page(determination)
        self.assertContains(response, determination.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))

    def test_lead_can_access_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        determination = DeterminationFactory(submission=submission, author=self.user, not_draft=True)
        response = self.get_page(determination)
        self.assertContains(response, determination.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))


class DeterminationFormTestCase(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:determinations:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_form_if_lead(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        response = self.get_page(submission, 'form')
        self.assertContains(response, submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))

    def test_cant_access_wrong_status(self):
        submission = ApplicationSubmissionFactory(status='more_info')
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)

    def test_cant_resubmit_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        determination = DeterminationFactory(submission=submission, author=self.user, submitted=True)
        response = self.post_page(submission, {'data': 'value', 'outcome': determination.outcome}, 'form')
        self.assertRedirects(response, self.url(submission))

    def test_can_edit_draft_determination(self):
        submission = ApplicationSubmissionFactory(status='post_review_discussion', lead=self.user)
        DeterminationFactory(submission=submission, author=self.user)
        response = self.post_page(submission, {
            'data': 'value',
            'outcome': ACCEPTED,
            'message': 'Accepted determination draft message',
            'save_draft': True,
        }, 'form')
        self.assertContains(response, '[Draft] Approved')
        self.assertContains(response, reverse(self.url_name.format('form'), kwargs=self.get_kwargs(submission)))
        self.assertNotContains(response, 'Accepted determination draft message')

    def test_cannot_edit_draft_determination_if_not_lead(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        determination = DeterminationFactory(submission=submission, author=self.user, accepted=True)
        response = self.post_page(submission, {'data': 'value', 'outcome': determination.outcome}, 'form')
        self.assertRedirects(response, self.url(submission))

    def test_sends_message_if_requires_more_info(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        determination = DeterminationFactory(submission=submission, author=self.user)
        determination_message = 'This is the message'
        self.post_page(
            submission,
            {'data': 'value', 'outcome': determination.outcome, 'message': determination_message},
            'form',
        )
        self.assertEqual(Activity.comments.count(), 1)
        self.assertEqual(Activity.comments.first().message, determination_message)

    def test_can_progress_stage_via_determination(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, lead=self.user)

        response = self.post_page(submission, {
            'data': 'value',
            'outcome': ACCEPTED,
            'message': 'You are invited to submit a proposal',
        }, 'form')

        # Cant use refresh from DB with FSM
        submission_original = self.refresh(submission)
        submission_next = submission_original.next

        # Cannot use self.url() as that uses a different base.
        url = reverse('funds:submissions:detail', kwargs={'pk': submission_next.id})
        self.assertRedirects(response, self.factory.get(url, secure=True).build_absolute_uri(url))
        self.assertEqual(submission_original.status, 'invited_to_proposal')
        self.assertEqual(submission_next.status, 'draft_proposal')


class UserDeterminationFormTestCase(BaseViewTestCase):
    user_factory = UserFactory
    url_name = 'funds:submissions:determinations:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_cant_access_form(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)
