from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlparse

from django.conf import settings
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.signing import TimestampSigner, dumps, loads
from django.test import TestCase, override_settings
from django.urls import reverse

from .factories import OAuthUserFactory, StaffFactory, UserFactory

EMAIL_CHANGE_URL = reverse("users:email_change_confirm_password")
ELEVATE_URL = reverse("users:elevate")
CONFIRM_LINK_SENT_URL = reverse("users:confirm_link_sent")
ACCOUNT_URL = reverse("users:account")


def make_signed_value(updated_email):
    """Build the signed query-string value that the profile form produces."""
    return TimestampSigner().sign(dumps({"updated_email": updated_email}))


def url_with_value(signed_value):
    return f"{EMAIL_CHANGE_URL}?{urlencode({'value': signed_value})}"


class TestEmailChangeRequiresLogin(TestCase):
    def test_unauthenticated_user_redirected_to_login(self):
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
        signed = make_signed_value(self.user.email)
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )

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

    def test_email_in_use_sends_notice_instead_of_confirmation(self):
        from django.core import mail

        other_user = UserFactory()
        signed = make_signed_value(other_user.email.upper())
        response = self.client.get(url_with_value(signed), follow=False)
        # Same response as a normal change, so nothing is revealed on screen.
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )
        self.assertEqual(len(mail.outbox), 2)
        notice = mail.outbox[1]
        self.assertEqual(notice.to, [other_user.email.upper()])
        self.assertIn("already an account", notice.body)
        confirm_path_prefix = confirm_url("x").removesuffix("x/")
        self.assertNotIn(confirm_path_prefix, notice.body)


class TestProfileFormEmailChange(TestCase):
    """The profile form must not reveal whether an email is registered."""

    def setUp(self):
        self.user = UserFactory()
        # The first backend is OAuth, which disables the email field.
        self.client.force_login(self.user, backend=settings.CUSTOM_AUTH_BACKEND)

    def post_profile(self, email, full_name=None):
        return self.client.post(
            ACCOUNT_URL,
            {"full_name": full_name or self.user.full_name, "email": email},
            follow=False,
        )

    def test_email_in_use_goes_to_change_flow(self):
        other_user = UserFactory()
        response = self.post_profile(other_user.email)
        self.assertEqual(response.status_code, 302)
        self.assertIn(EMAIL_CHANGE_URL, response["Location"])

    def test_new_email_goes_to_change_flow(self):
        response = self.post_profile("unused@example.com")
        self.assertEqual(response.status_code, 302)
        self.assertIn(EMAIL_CHANGE_URL, response["Location"])

    def test_other_edits_saved_before_email_confirmed(self):
        old_email = self.user.email
        self.post_profile("unused@example.com", full_name="New Name")
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "New Name")
        self.assertEqual(self.user.email, old_email)

    def test_other_edits_saved_when_email_in_use(self):
        old_email = self.user.email
        other_user = UserFactory()
        self.post_profile(other_user.email, full_name="New Name")
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "New Name")
        self.assertEqual(self.user.email, old_email)

    def test_signed_value_carries_only_the_email(self):
        response = self.post_profile("unused@example.com", full_name="New Name")
        value = parse_qs(urlparse(response["Location"]).query)["value"][0]
        payload = loads(TimestampSigner().unsign(value))
        self.assertEqual(payload, {"updated_email": "unused@example.com"})


class TestProfileFormEmailChangeStaff(TestCase):
    def setUp(self):
        self.user = StaffFactory()
        self.client.force_login(self.user, backend=settings.CUSTOM_AUTH_BACKEND)

    def test_slack_saved_before_email_confirmed(self):
        self.client.post(
            ACCOUNT_URL,
            {
                "full_name": self.user.full_name,
                "email": "unused@example.com",
                "slack": "@newslack",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.slack, "@newslack")


class TestEmailChangeElevatedUserWithPassword(TestCase):
    """A user with a password who has elevated their session can proceed."""

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_elevated_user_can_complete_email_change(self):
        signed = make_signed_value(self.user.email)
        with patch(
            "hypha.elevate.middleware.has_elevated_privileges", return_value=True
        ):
            response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )


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
