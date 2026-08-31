from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from hypha.apply.utils.testing.tests import BaseViewTestCase

from ..models import PendingSignup
from ..tokens import PasswordlessLoginTokenGenerator, PasswordlessSignupTokenGenerator
from .factories import OAuthUserFactory, StaffFactory, SuperUserFactory, UserFactory


def make_uid(obj):
    return urlsafe_base64_encode(force_bytes(obj.pk))


class BaseTestProfielView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("users:account")


class TestProfileView(BaseTestProfielView):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_cant_access_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url, follow=True)
        # Initial redirect will be via to https through a 301
        self.assertRedirects(
            response,
            reverse(settings.LOGIN_URL) + "?next=" + self.url,
        )

    def test_has_required_text_and_buttons(self):
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, reverse("users:password_change"))
        self.assertContains(response, "Enable 2FA")
        self.assertContains(response, reverse("two_factor:setup"))
        self.assertNotContains(response, "Slack name")

    def test_doesnt_includes_change_password_for_oauth(self):
        self.client.force_login(OAuthUserFactory())
        response = self.client.get(self.url, follow=True)
        self.assertNotContains(response, reverse("users:password_change"))

    def test_2fa_setup_view(self):
        response = self.client.get(reverse("two_factor:setup"), follow=True)
        self.assertContains(response, "I've installed a 2FA App")

        response = self.client.post(
            reverse("two_factor:setup"),
            follow=True,
            data={"setup_view-current_step": "welcome"},
        )
        assert "Verification code:" in response.content.decode("utf-8")


class TestStaffProfileView(BaseTestProfielView):
    def setUp(self):
        self.staff = StaffFactory()
        self.client.force_login(self.staff)

    def test_can_set_slack_name(self):
        response = self.client.get(self.url, follow=True)
        self.assertContains(response, "Slack name")


class TestPasswordReset(BaseViewTestCase):
    user_factory = UserFactory
    url_name = "users:{}"
    base_view_name = "password_reset"

    def test_receives_email(self):
        response = self.post_page(None, data={"email": self.user.email})
        self.assertRedirects(response, self.url(None, view_name="password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "https://testserver/account/password/reset/confirm", mail.outbox[0].body
        )


class TestBecome(TestCase):
    def setUp(self):
        self.staff = StaffFactory()
        self.user = UserFactory()
        self.superuser = SuperUserFactory()

    def become_request(self, user, target):
        self.client.force_login(user)
        url = reverse("hijack-become")
        response = self.client.post(
            url, {"user_pk": target.pk}, follow=True, secure=True
        )
        return response

    def test_staff_cannot_become_user(self):
        response = self.become_request(self.staff, self.user)
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_become_superuser(self):
        response = self.become_request(self.staff, self.superuser)
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_become_staff(self):
        response = self.become_request(self.superuser, self.staff)
        self.assertEqual(response.status_code, 200)

    def test_superuser_cannot_become_superuser(self):
        other_superuser = SuperUserFactory()
        response = self.become_request(self.superuser, other_superuser)
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_become_staff(self):
        response = self.become_request(self.user, self.staff)
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_become_other_user(self):
        other_user = UserFactory()
        response = self.become_request(self.user, other_user)
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_become_superuser(self):
        response = self.become_request(self.user, self.superuser)
        self.assertEqual(response.status_code, 403)


class TestActivationView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.token_generator = PasswordResetTokenGenerator()
        self.uid = make_uid(self.user)
        self.token = self.token_generator.make_token(self.user)
        self.url = reverse(
            "users:activate",
            kwargs={"uidb64": self.uid, "token": self.token},
        )

    def test_get_valid_token_shows_confirmation_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/activation/confirm.html")

    def test_get_invalid_token_shows_invalid_page(self):
        url = reverse(
            "users:activate",
            kwargs={"uidb64": self.uid, "token": "invalid-token"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_get_invalid_uid_shows_invalid_page(self):
        url = reverse(
            "users:activate",
            kwargs={"uidb64": "aaaaaa", "token": self.token},
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_post_valid_token_logs_user_in(self):
        response = self.client.post(self.url, follow=True)
        self.assertEqual(response.status_code, 200)
        # Should redirect to create_password page
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_post_invalid_token_shows_invalid_page(self):
        url = reverse(
            "users:activate",
            kwargs={"uidb64": self.uid, "token": "invalid-token"},
        )
        response = self.client.post(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_post_valid_token_redirects_to_set_password(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse("users:activate_password"),
            fetch_redirect_response=False,
        )

    def test_post_valid_token_with_next_includes_redirect(self):
        url = self.url + "?next=/dashboard/"
        response = self.client.post(url)
        self.assertIn("/dashboard/", response["Location"])


class TestPasswordlessLoginView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.token_generator = PasswordlessLoginTokenGenerator()
        self.uid = make_uid(self.user)
        self.token = self.token_generator.make_token(self.user)
        self.url = reverse(
            "users:do_passwordless_login",
            kwargs={"uidb64": self.uid, "token": self.token},
        )

    def test_get_valid_token_shows_confirmation_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/activation/confirm.html")

    def test_get_invalid_token_shows_invalid_page(self):
        url = reverse(
            "users:do_passwordless_login",
            kwargs={"uidb64": self.uid, "token": "bad-token"},
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_get_invalid_uid_shows_invalid_page(self):
        url = reverse(
            "users:do_passwordless_login",
            kwargs={"uidb64": "notvalid", "token": self.token},
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_post_valid_token_logs_user_in_and_redirects(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
            fetch_redirect_response=False,
        )
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_post_invalid_token_shows_invalid_page(self):
        url = reverse(
            "users:do_passwordless_login",
            kwargs={"uidb64": self.uid, "token": "bad-token"},
        )
        response = self.client.post(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_post_with_redirect_url_follows_next(self):
        url = self.url + "?next=/dashboard/"
        response = self.client.post(url, {"next": "/dashboard/"})
        self.assertRedirects(response, "/dashboard/", fetch_redirect_response=False)


class TestPasswordlessSignupView(TestCase):
    def setUp(self):
        self.pending = PendingSignup.objects.create(
            email="newuser@example.com", token="randomtoken123456"
        )
        self.token_generator = PasswordlessSignupTokenGenerator()
        self.uid = make_uid(self.pending)
        self.token = self.token_generator.make_token(self.pending)
        self.url = reverse(
            "users:do_passwordless_signup",
            kwargs={"uidb64": self.uid, "token": self.token},
        )

    def test_get_valid_token_shows_confirmation_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/activation/confirm.html")

    def test_get_invalid_token_shows_invalid_page(self):
        url = reverse(
            "users:do_passwordless_signup",
            kwargs={"uidb64": self.uid, "token": "bad-token"},
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_get_invalid_uid_shows_invalid_page(self):
        url = reverse(
            "users:do_passwordless_signup",
            kwargs={"uidb64": "notvalid", "token": self.token},
        )
        response = self.client.get(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")

    def test_post_valid_token_creates_user(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        self.client.post(self.url)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_post_valid_token_deletes_pending_signup(self):
        self.client.post(self.url)
        self.assertFalse(PendingSignup.objects.filter(pk=self.pending.pk).exists())

    def test_post_valid_token_logs_user_in(self):
        response = self.client.post(self.url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_post_valid_token_redirects_to_dashboard(self):
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            reverse("dashboard:dashboard"),
            fetch_redirect_response=False,
        )

    def test_post_invalid_token_shows_invalid_page(self):
        url = reverse(
            "users:do_passwordless_signup",
            kwargs={"uidb64": self.uid, "token": "bad-token"},
        )
        response = self.client.post(url)
        self.assertTemplateUsed(response, "users/activation/invalid.html")
