from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from hypha.apply.users.tests.factories import UserFactory

from ..middleware import ALLOWED_SUBPATH_FOR_UNVERIFIED_USERS


@override_settings(ROOT_URLCONF="hypha.apply.urls", ENFORCE_TWO_FACTOR=True)
class TestTwoFactorAuthenticationMiddleware(TestCase):
    def enable_otp(self, user):
        return user.totpdevice_set.create(name="default")

    def test_unverified_user_redirect(self):
        user = UserFactory()
        self.client.force_login(user)

        response = self.client.get(settings.LOGIN_REDIRECT_URL, follow=True)
        self.assertRedirects(
            response, reverse("users:two_factor_required"), status_code=301
        )

        response = self.client.get(reverse("funds:submissions:list"), follow=True)
        self.assertRedirects(
            response, reverse("users:two_factor_required"), status_code=301
        )

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

        for path in ALLOWED_SUBPATH_FOR_UNVERIFIED_USERS:
            response = self.client.get(path, follow=True)
            self.assertEqual(response.status_code, 200)
