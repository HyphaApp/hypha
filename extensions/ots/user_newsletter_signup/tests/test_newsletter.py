from django.test import TestCase
from django.urls import reverse

from hypha.apply.users.tests.factories import SuperUserFactory, UserFactory


class TestProfileViewNewsletter(TestCase):
    def test_newsletter_on_profile_page(self):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(reverse("users:account"), follow=True)
        self.assertContains(response, "like to receive occasional emails")

    def test_newsletter_on_user_add_page(self):
        user = SuperUserFactory()
        self.client.force_login(user)
        response = self.client.get(reverse("wagtailusers_users:add"), follow=True)
        self.assertContains(response, "newsletter")
