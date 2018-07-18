from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse

from ..forms import ProfileForm
from .factories import OAuthUserFactory, StaffFactory, UserFactory


class BaseTestProfielView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('users:account')

    def form_data(self, user, **values):
        fields = ProfileForm.Meta.fields
        data = model_to_dict(user, fields)
        data.update(**values)
        return data


class TestProfileView(BaseTestProfielView):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_cant_acces_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('users:login') + '?next=' + self.url)

    def test_includes_change_password(self):
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
        data = self.form_data(self.user, email=new_email)
        self.client.post(self.url, data=data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, new_email)

    def test_cant_set_slack_name(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'Slack Name')

        slack_name = '@foobar'
        data = self.form_data(self.user, slack=slack_name)
        self.client.post(self.url, data=data)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.slack, slack_name)


class TestStaffProfileView(BaseTestProfielView):
    def setUp(self):
        self.staff = StaffFactory()
        self.client.force_login(self.staff)

    def test_can_set_slack_name(self):
        slack_name = '@foobar'
        data = self.form_data(self.staff, slack=slack_name)

        self.client.post(self.url, data=data)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)

    def test_can_set_slack_name_with_trailing_space(self):
        slack_name = '@foobar'
        data = self.form_data(self.staff, slack=slack_name + ' ')

        self.client.post(self.url, data=data)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)

    def test_cant_set_slack_name_with_space(self):
        slack_name = '@ foobar'
        data = self.form_data(self.staff, slack=slack_name)

        self.client.post(self.url, data=data)
        self.staff.refresh_from_db()
        self.assertNotEqual(self.staff.slack, slack_name)

    def test_auto_prepend_at(self):
        slack_name = 'foobar'
        data = self.form_data(self.staff, slack=slack_name)

        self.client.post(self.url, data=data)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, '@' + slack_name)

    def test_can_clear_slack_name(self):
        slack_name = ''
        data = self.form_data(self.staff, slack=slack_name)

        self.client.post(self.url, data=data)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.slack, slack_name)
