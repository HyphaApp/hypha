from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlparse

from django.conf import settings
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.signing import TimestampSigner
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from ..models import ConfirmAccessToken
from ..views import EMAIL_CHANGE_CONFIRM_SALT, EMAIL_CHANGE_REQUEST_SALT
from .factories import StaffFactory, UserFactory

EMAIL_CHANGE_URL = reverse("users:email_change_confirm_password")
ELEVATE_URL = reverse("users:elevate")
CONFIRM_LINK_SENT_URL = reverse("users:confirm_link_sent")
ACCOUNT_URL = reverse("users:account")
NEW_EMAIL = "newemail@example.com"


def make_signed_value(user, updated_email):
    """Build the signed query-string value that the profile form produces."""
    return TimestampSigner(salt=EMAIL_CHANGE_REQUEST_SALT).sign_object(
        {"pk": user.pk, "updated_email": updated_email}
    )


def url_with_value(signed_value):
    return f"{EMAIL_CHANGE_URL}?{urlencode({'value': signed_value})}"


def elevate_session(testcase):
    """Treat the test client's session as elevated for the rest of the test."""
    patcher = patch(
        "hypha.elevate.middleware.has_elevated_privileges", return_value=True
    )
    patcher.start()
    testcase.addCleanup(patcher.stop)


class TestEmailChangeRequiresLogin(TestCase):
    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(EMAIL_CHANGE_URL, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse(settings.LOGIN_URL), response["Location"])


class TestEmailChangeElevationCheck(TestCase):
    """Users must re-authenticate (elevate) before proceeding."""

    def setUp(self):
        self.user = UserFactory()  # has a usable password
        self.client.force_login(self.user)

    def test_unelevated_user_redirected_to_elevate(self):
        signed = make_signed_value(self.user, NEW_EMAIL)
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(ELEVATE_URL, response["Location"])

    def test_elevate_redirect_preserves_next_url(self):
        signed = make_signed_value(self.user, NEW_EMAIL)
        target = url_with_value(signed)
        response = self.client.get(target, follow=False)
        self.assertIn(EMAIL_CHANGE_URL, response["Location"])

    def test_elevated_user_is_not_redirected_to_elevate(self):
        signed = make_signed_value(self.user, NEW_EMAIL)
        with patch(
            "hypha.elevate.middleware.has_elevated_privileges", return_value=True
        ):
            response = self.client.get(url_with_value(signed), follow=False)
        self.assertNotEqual(response["Location"], ELEVATE_URL)


class TestEmailChangePasswordlessUserMustElevate(TestCase):
    """Users without a usable password must also elevate, via an emailed code."""

    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.user.set_unusable_password()
        self.user.save()
        # Passwordless users log in with an emailed code, through the custom
        # backend. The first backend is OAuth, which disables the email field.
        self.client.force_login(self.user, backend=settings.CUSTOM_AUTH_BACKEND)

    def test_email_change_is_held_until_elevated_with_emailed_code(self):
        from django.core import mail

        response = self.client.post(
            ACCOUNT_URL, {"full_name": self.user.full_name, "email": NEW_EMAIL}
        )
        change_url = response["Location"]
        self.assertIn(EMAIL_CHANGE_URL, change_url)

        response = self.client.get(change_url)
        self.assertIn(ELEVATE_URL, response["Location"])
        self.assertEqual(len(mail.outbox), 0)

        # With no password to enter, the elevate page offers an emailed code.
        send_code_url = reverse("users:elevate_send_confirm_access_email")
        self.assertContains(self.client.get(response["Location"]), send_code_url)

        next_query = urlencode({"next": change_url})
        self.client.post(f"{send_code_url}?{next_query}")
        code = ConfirmAccessToken.objects.get(user=self.user).token
        response = self.client.post(
            f"{reverse('users:elevate_check_code')}?{next_query}", {"code": code}
        )
        self.assertEqual(response["HX-Redirect"], change_url)

        mail.outbox.clear()
        response = self.client.get(change_url)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )
        self.assertIn(NEW_EMAIL, [addr for msg in mail.outbox for addr in msg.to])


class TestEmailChangeTokenValidation(TestCase):
    """The signed token in the query string must be valid, unexpired and requested by the same user that the change is being executed for."""

    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)
        elevate_session(self)

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
        self.assertContains(response, "expired or is invalid")


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class TestEmailChangeSuccess(TestCase):
    """With a valid elevated session and correct token, the view updates the user."""

    def setUp(self):
        cache.clear()
        self.user = UserFactory()
        self.client.force_login(self.user)
        elevate_session(self)

    def test_valid_token_redirects_to_confirm_link_sent(self):
        signed = make_signed_value(self.user, NEW_EMAIL)
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )

    def test_valid_token_sends_alert_email(self):
        from django.core import mail

        signed = make_signed_value(self.user, NEW_EMAIL)
        self.client.get(url_with_value(signed))
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_changed_email_sends_confirmation_email(self):
        from django.core import mail

        new_email = "newemail@example.com"
        signed = make_signed_value(self.user, new_email)
        self.client.get(url_with_value(signed))
        # Two emails: alert to old address + confirmation to new address
        self.assertEqual(len(mail.outbox), 2)
        all_recipients = [addr for msg in mail.outbox for addr in msg.to]
        self.assertIn(new_email, all_recipients)

    def test_same_email_sends_nothing(self):
        from django.core import mail

        signed = make_signed_value(self.user, self.user.email)  # same email
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(response, ACCOUNT_URL, fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_signed_value_can_only_be_used_once(self):
        from django.core import mail

        target = url_with_value(make_signed_value(self.user, NEW_EMAIL))
        self.client.get(target)
        sent = len(mail.outbox)
        response = self.client.get(target, follow=False)
        # A reload lands on the same "link sent" page, without sending again.
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )
        self.assertEqual(len(mail.outbox), sent)

    def test_signed_value_reusable_if_sending_fails(self):
        from django.core import mail

        target = url_with_value(make_signed_value(self.user, NEW_EMAIL))
        with patch(
            "hypha.apply.users.views.send_confirmation_email",
            side_effect=ConnectionError,
        ):
            with self.assertRaises(ConnectionError):
                self.client.get(target)
        mail.outbox.clear()
        response = self.client.get(target, follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )
        self.assertEqual(len(mail.outbox), 2)

    def test_confirmation_token_is_not_accepted_as_value(self):
        from django.core import mail

        token = make_confirmation_token(self.user, NEW_EMAIL)
        response = self.client.get(url_with_value(token), follow=False)
        self.assertRedirects(response, ACCOUNT_URL, fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_value_for_other_user_is_rejected(self):
        from django.core import mail

        signed = make_signed_value(UserFactory(), NEW_EMAIL)
        response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(response, ACCOUNT_URL, fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 0)

    def test_requests_are_rate_limited(self):
        statuses = [
            self.client.get(
                url_with_value(make_signed_value(self.user, f"new{i}@example.com"))
            ).status_code
            for i in range(6)
        ]
        self.assertEqual(statuses[-1], 403)

    def test_email_in_use_sends_notice_instead_of_confirmation(self):
        from django.core import mail

        other_user = UserFactory()
        signed = make_signed_value(self.user, other_user.email.upper())
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

    def test_plain_text_emails_are_not_html_escaped(self):
        from django.core import mail

        self.user.full_name = "Anna O'Brien"
        self.user.save()
        signed = make_signed_value(self.user, "o'brien@example.com")
        self.client.get(url_with_value(signed))
        alert, confirmation = mail.outbox
        self.assertIn("o'brien@example.com", alert.body)
        self.assertIn("Anna O'Brien", confirmation.body)

    def test_email_in_use_notice_is_not_html_escaped(self):
        from django.core import mail

        other_user = UserFactory(email="o'brien@example.com")
        signed = make_signed_value(self.user, other_user.email)
        self.client.get(url_with_value(signed))
        self.assertIn("o'brien@example.com", mail.outbox[1].body)


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

    def test_signed_value_carries_the_user_and_email(self):
        response = self.post_profile("unused@example.com", full_name="New Name")
        value = parse_qs(urlparse(response["Location"]).query)["value"][0]
        payload = TimestampSigner(salt=EMAIL_CHANGE_REQUEST_SALT).unsign_object(value)
        self.assertEqual(
            payload, {"pk": self.user.pk, "updated_email": "unused@example.com"}
        )


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
        signed = make_signed_value(self.user, NEW_EMAIL)
        with patch(
            "hypha.elevate.middleware.has_elevated_privileges", return_value=True
        ):
            response = self.client.get(url_with_value(signed), follow=False)
        self.assertRedirects(
            response, CONFIRM_LINK_SENT_URL, fetch_redirect_response=False
        )


def make_confirmation_token(user, updated_email, current_email=None, pk=None):
    """Build the signed token that goes into the confirmation email link."""
    return TimestampSigner(salt=EMAIL_CHANGE_CONFIRM_SALT).sign_object(
        {
            "pk": user.pk if pk is None else pk,
            "current_email": user.email if current_email is None else current_email,
            "updated_email": updated_email,
        }
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

    def test_request_value_is_not_accepted_as_token(self):
        token = TimestampSigner(salt=EMAIL_CHANGE_REQUEST_SALT).sign_object(
            {
                "pk": self.user.pk,
                "current_email": self.user.email,
                "updated_email": self.new_email,
            }
        )
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

        response = self.client.post(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, self.new_email)

    def test_token_for_address_taken_since_is_invalid(self):
        token = make_confirmation_token(self.user, self.new_email)
        UserFactory(email=self.new_email.upper())
        response = self.client.get(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        response = self.client.post(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()

    def test_save_integrity_error_shows_invalid_link(self):
        token = make_confirmation_token(self.user, self.new_email)
        with patch.object(self.user.__class__, "save", side_effect=IntegrityError):
            response = self.client.post(confirm_url(token))
        self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()

    def test_tampered_token_is_invalid(self):
        token = make_confirmation_token(self.user, self.new_email)
        for bad_token in (token[:-1] + ("A" if token[-1] != "A" else "B"), "garbage"):
            response = self.client.post(confirm_url(bad_token))
            self.assertTemplateUsed(response, "users/email_change/invalid_link.html")
        self.assertEmailUnchanged()
