import json

from django.test import TestCase

from hypha.apply.funds.tests.factories import (
    FundTypeFactory,
    LabFactory,
    RoundFactory,
    TodayRoundFactory,
)
from hypha.home.factories import ApplySiteFactory

OPEN_CALLS_URL = "/api/v2/open-calls.json"

# Default rate limit is 5/m — one more than the limit triggers a 403.
RATE_LIMIT = 5


class TestOpenCallsJson(TestCase):
    def setUp(self):
        ApplySiteFactory()

    def test_returns_200_for_anonymous_user(self):
        response = self.client.get(OPEN_CALLS_URL)
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_json(self):
        response = self.client.get(OPEN_CALLS_URL)
        self.assertIn("application/json", response["Content-Type"])

    def test_response_is_valid_json_list(self):
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_returns_empty_list_with_no_open_funds(self):
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        self.assertEqual(data, [])

    def test_includes_fund_with_open_round(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=True, description="desc")
        TodayRoundFactory(parent=fund)
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        titles = [item["title"] for item in data]
        self.assertIn(fund.title, titles)

    def test_excludes_fund_with_no_open_round(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=True, description="desc")
        RoundFactory(parent=fund, closed=True)
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        titles = [item["title"] for item in data]
        self.assertNotIn(fund.title, titles)

    def test_excludes_fund_not_listed_on_front_page(self):
        fund = FundTypeFactory(
            parent=None, list_on_front_page=False, description="desc"
        )
        TodayRoundFactory(parent=fund)
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        titles = [item["title"] for item in data]
        self.assertNotIn(fund.title, titles)

    def test_includes_live_lab(self):
        lab = LabFactory(parent=None, list_on_front_page=True, description="desc")
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        titles = [item["title"] for item in data]
        self.assertIn(lab.title, titles)

    def test_excludes_lab_not_listed_on_front_page(self):
        LabFactory(parent=None, list_on_front_page=False, description="desc")
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        self.assertEqual(data, [])

    def test_response_items_have_expected_keys(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=True, description="desc")
        TodayRoundFactory(parent=fund)
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        item = data[0]
        for key in ("title", "description", "image", "weight", "next_deadline", "url"):
            self.assertIn(key, item)

    def test_response_does_not_expose_private_fields(self):
        fund = FundTypeFactory(parent=None, list_on_front_page=True, description="desc")
        TodayRoundFactory(parent=fund)
        response = self.client.get(OPEN_CALLS_URL)
        data = json.loads(response.content)
        item = data[0]
        for private_field in ("slack_channel", "activity_digest_recipient_emails"):
            self.assertNotIn(private_field, item)


class TestOpenCallsJsonRateLimit(TestCase):
    """The open-calls endpoint is rate-limited by IP on all HTTP methods."""

    def setUp(self):
        ApplySiteFactory()

    def test_accessible_before_limit(self):
        response = self.client.get(OPEN_CALLS_URL)
        self.assertEqual(response.status_code, 200)

    def test_blocked_after_ip_limit_exceeded(self):
        for _ in range(RATE_LIMIT):
            self.client.get(OPEN_CALLS_URL)
        response = self.client.get(OPEN_CALLS_URL)
        self.assertEqual(response.status_code, 403)
