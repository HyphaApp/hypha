from urllib import parse
from unittest import mock
import re

from django.test import override_settings, TestCase
from django.urls import reverse

import responses


any_url = re.compile(".")


class TestNewsletterView(TestCase):
    url = reverse('newsletter:subscribe')

    def setUp(self):
        self.origin = 'https://testserver/'
        self.client.defaults = {'HTTP_ORIGIN': self.origin}

    def assertNewsletterRedirects(self, response, target_url, *args, **kwargs):
        url = response.redirect_chain[0][0]
        parts = parse.urlsplit(url)
        self.assertTrue(parts.query.startswith('newsletter-'))

        target_url = target_url + '?' + parts.query

        return self.assertRedirects(response, target_url, *args, **kwargs)

    def test_redirected_home_if_get(self):
        response = self.client.get(self.url, secure=True, follow=True)
        request = response.request
        self.assertRedirects(response, '{}://{}/'.format(request['wsgi.url_scheme'], request['SERVER_NAME']))

    @override_settings(
        MAILCHIMP_API_KEY='a' * 32,
        MAILCHIMP_LIST_ID='12345'
    )
    @responses.activate
    def test_can_subscribe(self):
        responses.add(responses.POST, any_url, json={'id': '1234'}, status=200)

        response = self.client.post(self.url, data={'email': 'email@email.com'}, secure=True, follow=True)
        self.assertNewsletterRedirects(response, self.origin)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('Thank you', str(messages[0]))

    def test_error_in_form(self):
        response = self.client.post(self.url, data={'email': 'email_is_bad.com'}, secure=True, follow=True)
        self.assertNewsletterRedirects(response, self.origin)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('errors with', str(messages[0]))

    @override_settings(
        MAILCHIMP_API_KEY='a' * 32,
        MAILCHIMP_LIST_ID='12345'
    )
    @responses.activate
    @mock.patch('opentech.public.mailchimp.views.logger')
    def test_error_with_mailchimp(self, logger):
        # Copied from the mailchimp playground
        response_data = {
            "title": "Invalid Resource",
            "status": 400,
            "detail": "Please provide a valid email address.",
        }
        responses.add(responses.POST, any_url, json=response_data, status=400)
        response = self.client.post(self.url, data={'email': 'email@email.com'}, secure=True, follow=True)

        self.assertNewsletterRedirects(response, self.origin)

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('problem', str(messages[0]))
        # See opentech/public/mailchimp/views.py warning()
        # logger.error.assert_called_once_with(response_data)
