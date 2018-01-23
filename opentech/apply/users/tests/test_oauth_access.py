from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse


class TestOAuthAccess(TestCase):

    def test_oauth_page_requires_login(self):
        """
        This checks that /account/oauth requires the user to be logged in
        """
        oauth_page = reverse('users:oauth')
        response = self.client.get(oauth_page, follow=True)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('users:oauth'), status_code=301, target_status_code=200)

    @override_settings()
    def test_oauth_not_set_up(self):
        del settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS

        self.login()
        response = self.client.get(reverse('users:oauth'), follow=True)
        self.assertEqual(response.status_code, 403)

    def test_oauth_user_email_not_whitelisted(self):
        self.login()
        response = self.client.get(reverse('users:oauth'), follow=True)
        self.assertEqual(response.status_code, 403)

    # @override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS=['email.com'])
    # def test_oauth_whitelisted_user_can_see_link_to_oauth_settings_page(self):
    #     self.login()

    #     response = self.client.get(reverse('users:account'), follow=True)
    #     self.assertContains(response, 'Manage OAuth')

    @override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS=['email.com'])
    def test_oauth_whitelisted_user_can_access_oauth_settings_page(self):
        """
        Checks that the test user can access the OAuth page as their email is whitelisted
        """
        self.login()

        response = self.client.get(reverse('users:oauth'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Google OAuth')
        self.assertNotContains(response, 'Disconnect Google OAuth')

        self.assertTemplateUsed(response, 'users/oauth.html')

    def login(self):
        user = get_user_model().objects.create_user(username='test', email='test@email.com', password='password')
        self.assertTrue(
            self.client.login(username='test', password='password')
        )

        return user
