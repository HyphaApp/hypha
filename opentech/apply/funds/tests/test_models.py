from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase

from opentech.apply.funds.workflow import SingleStage

from .factories import FundTypeFactory, RoundFactory


def days_from_today(days):
    return date.today() + timedelta(days=days)


class TestFundModel(TestCase):
    def test_can_access_workflow_class(self):
        fund = FundTypeFactory(parent=None)
        self.assertEqual(fund.workflow, 'single')
        self.assertEqual(fund.workflow_class, SingleStage)

    def test_no_open_rounds(self):
        fund = FundTypeFactory(parent=None)
        self.assertIsNone(fund.open_round)

    def test_open_ended_round(self):
        fund = FundTypeFactory(parent=None)
        open_round = RoundFactory(end_date=None, parent=fund)
        self.assertEqual(fund.open_round, open_round)

    def test_normal_round(self):
        fund = FundTypeFactory(parent=None)
        open_round = RoundFactory(parent=fund)
        self.assertEqual(fund.open_round, open_round)

    def test_closed_round(self):
        fund = FundTypeFactory(parent=None)
        yesterday = days_from_today(-1)
        last_week = days_from_today(-7)
        RoundFactory(start_date=last_week, end_date=yesterday, parent=fund)
        self.assertIsNone(fund.open_round)

    def test_round_not_open(self):
        fund = FundTypeFactory(parent=None)
        tomorrow = days_from_today(1)
        RoundFactory(start_date=tomorrow, parent=fund)
        self.assertIsNone(fund.open_round)

    def test_multiple_open_rounds(self):
        fund = FundTypeFactory(parent=None)
        open_round = RoundFactory(parent=fund)
        next_round_start = open_round.end_date + timedelta(days=1)
        RoundFactory(start_date=next_round_start, end_date=None, parent=fund)
        self.assertEqual(fund.open_round, open_round)


class TestRoundModel(TestCase):
    def setUp(self):
        self.fund = FundTypeFactory(parent=None)

    def make_round(self, **kwargs):
        data = {'parent': self.fund}
        data.update(kwargs)
        return RoundFactory(**data)

    def test_normal_start_end_doesnt_error(self):
        self.make_round()

    def test_end_before_start(self):
        yesterday = date.today() - timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.make_round(end_date=yesterday)

    def test_end_overlaps(self):
        existing_round = self.make_round()
        overlapping_end = existing_round.end_date - timedelta(1)
        start = existing_round.start_date - timedelta(1)
        with self.assertRaises(ValidationError):
            self.make_round(start_date=start, end_date=overlapping_end)

    def test_start_overlaps(self):
        existing_round = self.make_round()
        overlapping_start = existing_round.start_date + timedelta(1)
        end = existing_round.end_date + timedelta(1)
        with self.assertRaises(ValidationError):
            self.make_round(start_date=overlapping_start, end_date=end)

    def test_inside_overlaps(self):
        existing_round = self.make_round()
        overlapping_start = existing_round.start_date + timedelta(1)
        overlapping_end = existing_round.end_date - timedelta(1)
        with self.assertRaises(ValidationError):
            self.make_round(start_date=overlapping_start, end_date=overlapping_end)

    def test_other_fund_not_impacting(self):
        self.make_round()
        new_fund = FundTypeFactory(parent=None)
        # Will share the same start and end dates
        self.make_round(parent=new_fund)

    def test_can_create_without_end_date(self):
        self.make_round(end_date=None)

    def test_can_not_create_with_other_open_end_date(self):
        existing_round = self.make_round(end_date=None)
        start = existing_round.start_date + timedelta(1)
        with self.assertRaises(ValidationError):
            self.make_round(start_date=start, end_date=None)

    def test_can_not_overlap_with_normal_round(self):
        existing_round = self.make_round()
        overlapping_start = existing_round.end_date - timedelta(1)
        with self.assertRaises(ValidationError):
            self.make_round(start_date=overlapping_start, end_date=None)

    def test_can_not_overlap_clean(self):
        existing_round = self.make_round()
        overlapping_start = existing_round.end_date - timedelta(1)
        new_round = RoundFactory.build(start_date=overlapping_start, end_date=None)

        # we add on the parent page which gets included from a pre_create_hook
        new_round.parent_page = self.fund

        with self.assertRaises(ValidationError):
            new_round.clean()
