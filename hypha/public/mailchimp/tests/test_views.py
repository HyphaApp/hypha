import re
from unittest import mock
from urllib import parse

from django.test import TestCase, override_settings
from django.urls import reverse

any_url = re.compile(".")


class TestNewsletterView(TestCase):
    url = reverse('newsletter:subscribe')

    def setUp(self):
        self.origin = 'https://testserver/'

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
    def test_can_subscribe(self):
        with mock.patch("hypha.public.mailchimp.views.subscribe_to_mailchimp") as mc_mock:
            mc_mock.return_value = None
            response = self.client.post(self.url, data={'email': 'email@email.com'}, secure=True, follow=True)

            self.assertNewsletterRedirects(response, self.origin)

            mc_mock.assert_called_once_with(email='email@email.com', data={'fname': '', 'lname': ''})

    def test_error_in_form(self):
        with mock.patch("hypha.public.mailchimp.views.subscribe_to_mailchimp") as mc_mock:
            mc_mock.return_value = None
            response = self.client.post(self.url, data={'email': 'email_is_bad.com'}, secure=True, follow=True)
            self.assertNewsletterRedirects(response, self.origin)

            assert not mc_mock.called, 'method should not have been called'
