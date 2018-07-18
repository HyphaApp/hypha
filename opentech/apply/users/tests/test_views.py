from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse

from ..forms import ProfileForm
from .factories import OAuthUserFactory, StaffFactory, UserFactory


class TestProfileView(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.url = reverse('users:account')

    def form_data(self, user, **values):
        fields = ProfileForm.Meta.fields
        data = model_to_dict(user, fields)
        data.update(**values)
        return data

    def test_cant_acces_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('users:login') + '?next=' + self.url)

    def test_includes_change_password(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, reverse('users:password_change'))

    def test_doesnt_includes_change_password_for_oauth(self):
        self.client.force_login(OAuthUserFactory())
        response = self.client.get(self.url)
        self.assertNotContains(response, reverse('users:password_change'))

    def test_email_unique(self):
        other_user = UserFactory()
        data = self.form_data(self.user, email=other_user.email)
        self.client.post(self.url, data=data)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.email, other_user.email)

    def test_can_change_email(self):
        new_email = 'me@another.com'
        self.client.force_login(self.user)
        data = self.form_data(self.user, email=new_email)
        self.client.post(self.url, data=data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)

    def test_can_set_slack_name_if_staff(self):
        staff = StaffFactory()
        slack_name = '@foobar'
        data = self.form_data(staff, slack=slack_name)

        self.client.force_login(staff)
        self.client.post(self.url, data=data)
        staff.refresh_from_db()
        self.assertEqual(staff.slack, slack_name)

    def test_cant_set_slack_name(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Slack Name')

        slack_name = '@foobar'
        data = self.form_data(self.user, slack=slack_name)
        self.client.post(self.url, data=data)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.slack, slack_name)
