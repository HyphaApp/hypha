from hypha.apply.users.tests.factories import ReviewerFactory, StaffFactory, UserFactory
from hypha.apply.utils.testing.tests import BaseViewTestCase


class BaseAllRoundsViewTestCase(BaseViewTestCase):
    url_name = "funds:rounds:{}"
    base_view_name = "list"


class TestStaffRoundPage(BaseAllRoundsViewTestCase):
    user_factory = StaffFactory

    def test_can_access_page(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)


class TestReviewerAllRoundPage(BaseAllRoundsViewTestCase):
    user_factory = ReviewerFactory

    def test_cant_access_page(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 403)


class TestApplicantRoundPage(BaseAllRoundsViewTestCase):
    user_factory = UserFactory

    def test_cant_access_page(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 403)
