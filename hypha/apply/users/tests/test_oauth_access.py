from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class TestOAuthAccess(TestCase):
    def login(self):
        email = "test@email.com"
        password = "password"
        user = get_user_model().objects.create_user(email=email, password=password)
        logged_in = self.client.login(email=email, password=password)
        self.assertTrue(logged_in)
        return user

    def test_oauth_page_requires_login(self):
        """
        This checks that /account/oauth requires the user to be logged in
        """
        oauth_page = reverse("users:oauth")
        response = self.client.get(oauth_page, follow=True)
        self.assertRedirects(
            response,
            reverse(settings.LOGIN_URL) + "?next=" + reverse("users:oauth"),
            target_status_code=200,
        )

    @override_settings()
    def test_oauth_not_set_up(self):
        del settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS

        self.login()
        response = self.client.get(reverse("users:oauth"), follow=True)
        self.assertEqual(response.status_code, 403)

    def test_oauth_user_email_not_whitelisted(self):
        self.login()
        response = self.client.get(reverse("users:oauth"), follow=True)
        self.assertEqual(response.status_code, 403)

    @override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS=["email.com"])
    def test_oauth_whitelisted_user_can_see_link_to_oauth_settings_page(self):
        self.login()

        response = self.client.get(reverse("users:account"), follow=True)
        self.assertNotContains(response, "Manage OAuth")

    @override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS=["email.com"])
    def test_oauth_whitelisted_user_can_access_oauth_settings_page(self):
        """
        Checks that the test user can access the OAuth page as their email is whitelisted
        """
        self.login()

        response = self.client.get(reverse("users:oauth"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google OAuth")
        self.assertNotContains(response, "Disconnect Google OAuth")

        self.assertTemplateUsed(response, "users/oauth.html")

    @override_settings(
        SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS=[],
        SOCIAL_AUTH_OKTA_OAUTH2_WHITELISTED_DOMAINS=["email.com"],
    )
    def test_oauth_okta_whitelisted_user_can_access_oauth_settings_page(self):
        """
        Checks that a user whose email is whitelisted for Okta (but not Google)
        can still access the OAuth page
        """
        self.login()

        response = self.client.get(reverse("users:oauth"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/oauth.html")


@override_settings(
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY="google-key",
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET="google-secret",
    SOCIAL_AUTH_OKTA_OAUTH2_KEY="okta-key",
    SOCIAL_AUTH_OKTA_OAUTH2_SECRET="okta-secret",
    SOCIAL_AUTH_OKTA_OAUTH2_API_URL="https://example.okta.com/oauth2/default",
)
class TestOAuthLoginButtons(TestCase):
    """`social:begin` only accepts POST since social-auth-app-django 6.0."""

    def test_begin_rejects_get(self):
        response = self.client.get(reverse("social:begin", args=["google-oauth2"]))
        self.assertEqual(response.status_code, 405)

    def test_begin_redirects_to_provider_on_post(self):
        for backend, provider in [
            ("google-oauth2", "https://accounts.google.com/"),
            ("okta-oauth2", "https://example.okta.com/oauth2/default/v1/authorize"),
        ]:
            with self.subTest(backend=backend):
                response = self.client.post(reverse("social:begin", args=[backend]))
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith(provider))

    def test_login_page_posts_to_begin(self):
        response = self.client.get(reverse("users:login"))
        for backend in ["google-oauth2", "okta-oauth2"]:
            with self.subTest(backend=backend):
                self.assertContains(
                    response,
                    f'action="{reverse("social:begin", args=[backend])}"',
                )
                self.assertContains(response, f'form="{backend}-login-form"')

    def test_passwordless_login_page_posts_to_begin(self):
        response = self.client.get(reverse("users:passwordless_login_signup"))
        for backend in ["google-oauth2", "okta-oauth2"]:
            with self.subTest(backend=backend):
                self.assertContains(
                    response,
                    f'action="{reverse("social:begin", args=[backend])}"',
                )
                self.assertContains(response, f'form="{backend}-login-form"')

    def test_next_is_carried_over_by_the_oauth_form(self):
        """`do_auth()` only reads POST data, so `next` must be a form field."""
        response = self.client.get(reverse("users:login") + "?next=/dashboard/")
        self.assertContains(
            response, '<input type="hidden" name="next" value="/dashboard/">'
        )

        self.client.post(
            reverse("social:begin", args=["google-oauth2"]), {"next": "/dashboard/"}
        )
        self.assertEqual(self.client.session["next"], "/dashboard/")

    @override_settings(SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS=["email.com"])
    def test_account_oauth_page_posts_to_begin(self):
        user = get_user_model().objects.create_user(
            email="test@email.com", password="password"
        )
        self.client.force_login(user)

        response = self.client.get(reverse("users:oauth"))
        self.assertContains(
            response, f'action="{reverse("social:begin", args=["google-oauth2"])}"'
        )
