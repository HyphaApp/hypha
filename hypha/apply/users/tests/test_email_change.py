from unittest.mock import patch
from urllib.parse import urlencode

from django.core.signing import TimestampSigner, dumps
from django.test import TestCase
from django.urls import reverse

from .factories import OAuthUserFactory, UserFactory

EMAIL_CHANGE_URL = reverse("users:email_change_confirm_password")
ELEVATE_URL = reverse("users:elevate")
CONFIRM_LINK_SENT_URL = reverse("users:confirm_link_sent")
ACCOUNT_URL = reverse("users:account")


def make_signed_value(updated_email, name="Test User", slack=""):
    """Build the signed query-string value that the profile form produces."""
    signer = TimestampSigner()
    return signer.sign(
        dumps({"updated_email": updated_email, "name": name, "slack": slack})
    )


def url_with_value(signed_value):
    return f"{EMAIL_CHANGE_URL}?{urlencode({'value': signed_value})}"


class TestEmailChangeRequiresLogin(TestCase):
    def test_unauthenticated_user_redirected_to_login(self):
        from django.conf import settings

        response = self.client.get(EMAIL_CHANGE_URL, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.LOGIN_URL), response["Location"])


class TestEmailChangeElevationCheck(TestCase):
    """Users with a usable password must re-authenticate (elevate) before proceeding."""

    def setUp(self):
        self.user = UserFactory()  # has a usable password
        self.client.force_login(self.user)

    def test_unelevated_user_redirected_to_elevate(self):
        signed = make_signed_value(self.user.email)
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(ELEVATE_URL, response["Location"])

    def test_elevate_redirect_preserves_next_url(self):
        signed = make_signed_value(self.user.email)
        target = url_with_value(signed)
        response = self.client.get(target, follow=False)
        self.assertIn(EMAIL_CHANGE_URL, response["Location"])

    def test_elevated_user_is_not_redirected_to_elevate(self):
        signed = make_signed_value(self.user.email)
        with patch(
            "hypha.elevate.middleware.has_elevated_privileges", return_value=True
        ):
            response = self.client.get(url_with_value(signed), follow=False)
        self.assertNotEqual(response["Location"], ELEVATE_URL)


class TestEmailChangeOAuthUserSkipsElevation(TestCase):
    """OAuth users have no usable password — the elevation gate must be skipped."""

    def setUp(self):
        self.user = OAuthUserFactory()
        self.client.force_login(self.user)

    def test_oauth_user_not_redirected_to_elevate(self):
        signed = make_signed_value(self.user.email)
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertNotIn(ELEVATE_URL, response.get("Location", ""))


class TestEmailChangeTokenValidation(TestCase):
    """The signed token in the query string must be valid and unexpired."""

    def setUp(self):
        self.user = OAuthUserFactory()  # skip elevation
        self.client.force_login(self.user)

    def test_missing_value_param_redirects_to_account(self):
        response = self.client.get(EMAIL_CHANGE_URL, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(ACCOUNT_URL, response["Location"])

    def test_tampered_value_redirects_to_account(self):
        response = self.client.get(
            f"{EMAIL_CHANGE_URL}?value=tampered.invalid.token", follow=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(ACCOUNT_URL, response["Location"])

    def test_tampered_value_shows_error_message(self):
        response = self.client.get(
            f"{EMAIL_CHANGE_URL}?value=tampered.invalid.token", follow=True
        )
        self.assertContains(response, "timed out")


class TestEmailChangeSuccess(TestCase):
    """With a valid elevated session and correct token, the view updates the user."""

    def setUp(self):
        self.user = OAuthUserFactory()  # skip elevation
        self.client.force_login(self.user)

    def test_valid_token_redirects_to_confirm_link_sent(self):
        signed = make_signed_value(self.user.email, name="New Name")
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )

    def test_valid_token_updates_full_name(self):
        signed = make_signed_value(self.user.email, name="Updated Name")
        self.client.get(url_with_value(signed))
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")

    def test_valid_token_sends_alert_email(self):
        from django.core import mail

        signed = make_signed_value(self.user.email)
        self.client.get(url_with_value(signed))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_changed_email_sends_confirmation_email(self):
        from django.core import mail

        new_email = "newemail@example.com"
        signed = make_signed_value(new_email)
        self.client.get(url_with_value(signed))
        # Two emails: alert to old address + confirmation to new address
        self.assertEqual(len(mail.outbox), 2)
        all_recipients = [addr for msg in mail.outbox for addr in msg.to]
        self.assertIn(new_email, all_recipients)

    def test_same_email_does_not_send_confirmation_email(self):
        from django.core import mail

        signed = make_signed_value(self.user.email)  # same email
        self.client.get(url_with_value(signed))
        # Only alert email, no confirmation needed
        self.assertEqual(len(mail.outbox), 1)


class TestEmailChangeElevatedUserWithPassword(TestCase):
    """A user with a password who has elevated their session can proceed."""

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_elevated_user_can_complete_email_change(self):
        signed = make_signed_value(self.user.email, name="Elevated Name")
        with patch(
            "hypha.elevate.middleware.has_elevated_privileges", return_value=True
        ):
            response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )

    def test_elevated_user_name_is_updated(self):
        signed = make_signed_value(self.user.email, name="Elevated Name")
        with patch(
            "hypha.elevate.middleware.has_elevated_privileges", return_value=True
        ):
            self.client.get(url_with_value(signed))
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Elevated Name")
