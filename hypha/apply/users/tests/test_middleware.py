from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from hypha.apply.users.tests.factories import UserFactory

from ..middleware import TWO_FACTOR_EXEMPTED_PATH_PREFIXES


@override_settings(ENFORCE_TWO_FACTOR=True)
class TestTwoFactorAuthenticationMiddleware(TestCase):
    def enable_otp(self, user):
        return user.totpdevice_set.create(name="default")

    def test_unverified_user_redirect(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(settings.LOGIN_REDIRECT_URL, follow=True)
        assert "Permission Denied" in response.content.decode("utf-8")

        response = self.client.get(reverse("funds:submissions:list"), follow=True)
        assert "Permission Denied" in response.content.decode("utf-8")

    def test_verified_user_redirect(self):
        user = UserFactory()
        self.client.force_login(user)
        self.enable_otp(user=user)
        response = self.client.get(settings.LOGIN_REDIRECT_URL, follow=True)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("funds:submissions:list"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_unverified_user_can_access_allowed_urls(self):
        user = UserFactory()
        self.client.force_login(user)

        for path in TWO_FACTOR_EXEMPTED_PATH_PREFIXES:
            response = self.client.get(path, follow=True)
            self.assertEqual(response.status_code, 200)
