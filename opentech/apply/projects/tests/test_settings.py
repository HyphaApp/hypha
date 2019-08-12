from django.test import TestCase, override_settings

from opentech.apply.users.tests.factories import StaffFactory


class TestProjectFeatureFlag(TestCase):
    @override_settings(PROJECTS_ENABLED=False)
    def test_urls_404_when_turned_off(self):
        self.client.force_login(StaffFactory())

        response = self.client.get('/apply/projects/', follow=True)
        self.assertEqual(response.status_code, 404)

        response = self.client.get('/apply/projects/1/', follow=True)
        self.assertEqual(response.status_code, 404)
