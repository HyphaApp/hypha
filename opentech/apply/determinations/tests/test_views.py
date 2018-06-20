from django.test import TestCase, RequestFactory
from django.urls import reverse

from opentech.apply.determinations.models import ACCEPTED
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from .factories import DeterminationFactory
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory


class BaseTestCase(TestCase):
    url_name = ''
    user_factory = None

    def setUp(self):
        self.factory = RequestFactory()
        self.user = self.user_factory()
        self.client.force_login(self.user)

    def url(self, instance, view_name='detail'):
        full_url_name = self.url_name.format(view_name)
        url = reverse(full_url_name, kwargs=self.get_kwargs(instance))
        request = self.factory.get(url, secure=True)
        return request.build_absolute_uri()

    def get_page(self, instance, view_name='detail'):
        return self.client.get(self.url(instance, view_name), secure=True, follow=True)

    def post_page(self, instance, data, view_name='detail'):
        return self.client.post(self.url(instance, view_name), data, secure=True, follow=True)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)


class StaffDeterminationsTestCase(BaseTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:determinations:{}'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.submission.id}

    def test_can_access_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        determination = DeterminationFactory(submission=submission, author=self.user, not_draft=True)
        response = self.get_page(determination)
        self.assertContains(response, determination.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))
        self.assertFalse(response.context['can_view_extended_data'])

    def test_lead_can_access_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        determination = DeterminationFactory(submission=submission, author=self.user, not_draft=True)
        response = self.get_page(determination)
        self.assertContains(response, determination.submission.title)
        self.assertContains(response, self.user.full_name)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))
        self.assertTrue(response.context['can_view_extended_data'])

class DeterminationFormTestCase(BaseTestCase):
    user_factory = StaffFactory
    url_name = 'funds:submissions:determinations:{}'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_can_access_form_if_lead(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        response = self.get_page(submission, 'form')
        self.assertContains(response, submission.title)
        self.assertContains(response, reverse('funds:submissions:detail', kwargs={'pk': submission.id}))

    def test_cannot_access_form_if_not_lead(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)

    def test_cant_access_wrong_status(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)

    def test_cant_resubmit_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        determination = DeterminationFactory(submission=submission, author=self.user, submitted=True)
        response = self.post_page(submission, {'data': 'value', 'outcome': determination.outcome}, 'form')
        self.assertTrue(response.context['has_determination_response'])
        self.assertContains(response, 'You have already added a determination for this submission')

    def test_can_edit_draft_determination(self):
        submission = ApplicationSubmissionFactory(status='in_discussion', lead=self.user)
        DeterminationFactory(submission=submission, author=self.user)
        response = self.post_page(submission, {
            'data': 'value',
            'outcome': ACCEPTED,
            'message': 'Accepted determination draft message',
            'save_draft': True
        }, 'form')
        self.assertContains(response, 'Accepted')
        self.assertContains(response, reverse(self.url_name.format('form'), kwargs=self.get_kwargs(submission)))
        self.assertContains(response, 'Accepted determination draft message')

    def test_cannot_edit_draft_determination_if_not_lead(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        determination = DeterminationFactory(submission=submission, author=self.user)
        response = self.post_page(submission, {'data': 'value', 'outcome': determination.outcome}, 'form')
        self.assertEqual(response.status_code, 403)


class UserDeterminationFormTestCase(BaseTestCase):
    user_factory = UserFactory
    url_name = 'funds:submissions:determinations:{}'

    def get_kwargs(self, instance):
        return {'submission_pk': instance.id}

    def test_cant_access_form(self):
        submission = ApplicationSubmissionFactory(status='in_discussion')
        response = self.get_page(submission, 'form')
        self.assertEqual(response.status_code, 403)
