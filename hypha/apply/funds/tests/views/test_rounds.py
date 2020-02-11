from opentech.apply.funds.tests.factories import (
    LabFactory,
    RoundFactory,
)

from opentech.apply.users.tests.factories import (
    ReviewerFactory,
    StaffFactory,
    UserFactory,
)
from opentech.apply.utils.testing.tests import BaseViewTestCase


class BaseAllRoundsViewTestCase(BaseViewTestCase):
    url_name = 'funds:rounds:{}'
    base_view_name = 'list'


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


class ByRoundTestCase(BaseViewTestCase):
    url_name = 'apply:rounds:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        try:
            return {'pk': instance.id}
        except AttributeError:
            return {'pk': instance['id']}


class TestStaffSubmissionByRound(ByRoundTestCase):
    user_factory = StaffFactory

    def test_can_access_round_page(self):
        new_round = RoundFactory()
        response = self.get_page(new_round)
        self.assertContains(response, new_round.title)

    def test_can_access_lab_page(self):
        new_lab = LabFactory()
        response = self.get_page(new_lab)
        self.assertContains(response, new_lab.title)

    def test_cant_access_normal_page(self):
        new_round = RoundFactory()
        page = new_round.get_site().root_page
        response = self.get_page(page)
        self.assertEqual(response.status_code, 404)

    def test_cant_access_non_existing_page(self):
        response = self.get_page({'id': 555})
        self.assertEqual(response.status_code, 404)


class TestApplicantSubmissionByRound(ByRoundTestCase):
    user_factory = UserFactory

    def test_cant_access_round_page(self):
        new_round = RoundFactory()
        response = self.get_page(new_round)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_lab_page(self):
        new_lab = LabFactory()
        response = self.get_page(new_lab)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_normal_page(self):
        new_round = RoundFactory()
        page = new_round.get_site().root_page
        response = self.get_page(page)
        self.assertEqual(response.status_code, 403)

    def test_cant_access_non_existing_page(self):
        response = self.get_page({'id': 555})
        self.assertEqual(response.status_code, 403)
