from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from hypha.apply.funds.tests.factories import FundTypeFactory
from hypha.apply.utils.testing import make_request


class TestRegistration(TestCase):
    @override_settings(ENABLE_PUBLIC_SIGNUP=False)
    def test_registration_enabled_has_no_link(self):
        response = self.client.get("/", follow=True)
        self.assertNotContains(response, reverse("users:register"))

    @override_settings(ENABLE_PUBLIC_SIGNUP=True)
    def test_registration_enabled_has_link(self):
        response = self.client.get("/", follow=True)
        self.assertContains(response, reverse("users:register"))

    @override_settings(ENABLE_PUBLIC_SIGNUP=True)
    def test_registration(self):
        response = self.client.post(
            reverse("users:register"),
            data={
                "email": "test@test.com",
                "first_name": "Not used - see full_name",
                "last_name": "Not used - see full_name",
            },
            secure=True,
        )
        assert len(mail.outbox) == 1
        assert "Activate your account on the" in mail.outbox[0].body

        assert response.status_code == 302
        assert reverse("users:register-success") in response.url

    @override_settings(ENABLE_PUBLIC_SIGNUP=True)
    def test_duplicate_registration_fails(self):
        response = self.client.post(
            reverse("users:register"),
            data={
                "email": "test@test.com",
                "first_name": "Not used - see full_name",
                "last_name": "Not used - see full_name",
            },
            secure=True,
        )
        mail.outbox.clear()

        response = self.client.post(
            reverse("users:register"),
            data={
                "email": "test@test.com",
                "first_name": "Not used - see full_name",
                "last_name": "Not used - see full_name",
            },
            secure=True,
        )

        assert len(mail.outbox) == 0
        self.assertContains(response, "A user with that email already exists")

    @override_settings(FORCE_LOGIN_FOR_APPLICATION=True, ENABLE_PUBLIC_SIGNUP=False)
    def test_force_login(self):
        fund = FundTypeFactory()
        response = fund.serve(
            make_request(None, {}, method="get", site=fund.get_site())
        )
        assert response.status_code == 302
        assert response.url == reverse(settings.LOGIN_URL) + "?next=/"
