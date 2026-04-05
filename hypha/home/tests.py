from django.test import TestCase
from django.urls import reverse

from hypha.apply.funds.tests.factories import (
    FundTypeFactory,
    LabFactory,
    RoundFactory,
    TodayRoundFactory,
)
from hypha.apply.users.tests.factories import StaffFactory
from hypha.home.factories import ApplySiteFactory


class TestHomeView(TestCase):
    def setUp(self):
        ApplySiteFactory()

    def test_home_returns_200_for_anonymous_user(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home/home.html")

    def test_home_context_contains_funds_key(self):
        response = self.client.get(reverse("home"))
        self.assertIn("funds", response.context)

    def test_home_funds_empty_with_no_open_rounds(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["funds"], [])

    def test_home_includes_fund_with_open_round(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=True)
        TodayRoundFactory(parent=fund)
        response = self.client.get(reverse("home"))
        self.assertIn(fund, response.context["funds"])

    def test_home_excludes_fund_with_no_open_round(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=True)
        # Closed round
        RoundFactory(parent=fund, closed=True)
        response = self.client.get(reverse("home"))
        self.assertNotIn(fund, response.context["funds"])

    def test_home_excludes_fund_not_listed_on_front_page(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=False)
        TodayRoundFactory(parent=fund)
        response = self.client.get(reverse("home"))
        self.assertNotIn(fund, response.context["funds"])

    def test_home_includes_live_lab(self):
        lab = LabFactory(parent=None, list_on_front_page=True)
        response = self.client.get(reverse("home"))
        self.assertIn(lab, response.context["funds"])

    def test_home_excludes_lab_not_listed_on_front_page(self):
        LabFactory(parent=None, list_on_front_page=False)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["funds"], [])

    def test_home_returns_200_for_logged_in_user(self):
        user = StaffFactory()
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
