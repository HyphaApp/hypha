from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.signing import TimestampSigner, dumps
from django.test import TestCase, override_settings
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
    """The signed token in the query string must be valid, unexpired and requested by the same user that the change is being executed for."""

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
        # Only the alert to the existing address — nothing is sent anywhere else.
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            [addr for msg in mail.outbox for addr in msg.to], [self.user.email]
        )


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


def make_confirmation_token(user, updated_email, current_email=None, pk=None):
    """Build the signed token that goes into the confirmation email link."""
    return TimestampSigner().sign(
        dumps(
            {
                "pk": user.pk if pk is None else pk,
                "current_email": user.email if current_email is None else current_email,
                "updated_email": updated_email,
            }
        )
    )


def confirm_url(token):
    return reverse("users:confirm_email", kwargs={"token": token})


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class EmailChangeConfirmation(TestCase):
    """The confirmation link shows a page on GET and only applies the change on POST."""

    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.original_email = self.user.email
        self.new_email = f"new{self.user.email}"
        self.client.force_login(self.user)

    def assertEmailUnchanged(self):
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.original_email)

    def test_get_valid_token_shows_confirm_page_without_changing_email(self):
        token = make_confirmation_token(self.user, self.new_email)
        response = self.client.get(confirm_url(token))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/email_change/confirm.html")
        self.assertContains(response, self.new_email)
        self.assertEmailUnchanged()

    def test_post_valid_token_updates_email(self):
        token = make_confirmation_token(self.user, self.new_email)
        response = self.client.post(confirm_url(token))
        self.assertRedirects(response, ACCOUNT_URL, fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.new_email)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("email has been successfully updated", messages[0].message)

    def test_token_for_other_user_is_invalid(self):
        other_user = UserFactory()
        token = make_confirmation_token(
            other_user, self.new_email, current_email=self.user.email
        )
        response = self.client.get(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        response = self.client.post(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()

    def test_token_with_stale_current_email_is_invalid(self):
        token = make_confirmation_token(
            self.user, self.new_email, current_email="old@example.com"
        )
        response = self.client.post(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()

    def test_token_is_single_use(self):
        token = make_confirmation_token(self.user, self.new_email)
        self.client.post(confirm_url(token))

        # Even after switching back to the address the token was issued
        # against, the used token must not work again.
        self.user.refresh_from_db()
        self.user.email = self.original_email
        self.user.save()

        response = self.client.post(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()

    def test_tampered_token_is_invalid(self):
        token = make_confirmation_token(self.user, self.new_email)
        for bad_token in (token[:-1] + ("A" if token[-1] != "A" else "B"), "garbage"):
            response = self.client.post(confirm_url(bad_token))
            self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()

    def test_email_already_in_use_is_rejected(self):
        UserFactory(email=self.new_email)
        token = make_confirmation_token(self.user, self.new_email)
        response = self.client.post(confirm_url(token))
        self.assertRedirects(response, ACCOUNT_URL, fetch_redirect_response=False)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("already in use", messages[0].message)
        self.assertEmailUnchanged()
