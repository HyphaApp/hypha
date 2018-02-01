from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from wagtail.wagtailcore.models import Site

from opentech.apply.funds import blocks
from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.workflow import SingleStage

from .factories import (
    ApplicationFormFactory,
    FundFormFactory,
    FundTypeFactory,
    RoundFactory,
)


def days_from_today(days):
    return date.today() + timedelta(days=days)


class TestFundModel(TestCase):
    def setUp(self):
        self.fund = FundTypeFactory(parent=None)

    def test_can_access_workflow_class(self):
        self.assertEqual(self.fund.workflow, 'single')
        self.assertEqual(self.fund.workflow_class, SingleStage)

    def test_no_open_rounds(self):
        self.assertIsNone(self.fund.open_round)

    def test_open_ended_round(self):
        open_round = RoundFactory(end_date=None, parent=self.fund)
        self.assertEqual(self.fund.open_round, open_round)

    def test_normal_round(self):
        open_round = RoundFactory(parent=self.fund)
        self.assertEqual(self.fund.open_round, open_round)

    def test_closed_round(self):
        yesterday = days_from_today(-1)
        last_week = days_from_today(-7)
        RoundFactory(start_date=last_week, end_date=yesterday, parent=self.fund)
        self.assertIsNone(self.fund.open_round)

    def test_round_not_open(self):
        tomorrow = days_from_today(1)
        RoundFactory(start_date=tomorrow, parent=self.fund)
        self.assertIsNone(self.fund.open_round)

    def test_multiple_open_rounds(self):
        open_round = RoundFactory(parent=self.fund)
        next_round_start = open_round.end_date + timedelta(days=1)
        RoundFactory(start_date=next_round_start, end_date=None, parent=self.fund)
        self.assertEqual(self.fund.open_round, open_round)

    def test_can_not_be_open_with_draft_round(self):
        new_round = RoundFactory(parent=self.fund)
        new_round.live = False
        new_round.save()
        self.assertEqual(self.fund.open_round, None)


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


class TestFormSubmission(TestCase):
    def setUp(self):
        self.site = Site.objects.first()
        self.User = get_user_model()

        self.request_factory = RequestFactory()
        # set up application form with minimal requirement for creating user
        application_form = {
            'form_fields__0__email__': '',
            'form_fields__1__full_name__': '',
        }
        form = ApplicationFormFactory(**application_form)
        fund = FundTypeFactory()
        FundFormFactory(fund=fund, form=form)
        self.round_page = RoundFactory(parent=fund)

    def submit_form(self, email='', name='', user=AnonymousUser()):
        fields = self.round_page.get_form_fields()
        data = {k: v for k, v in zip(fields, [email, name])}

        request = self.request_factory.post('', data)
        request.user = user
        request.site = self.site

        return self.round_page.get_parent().serve(request)

    def test_can_submit_if_new(self):
        email = 'test@test.com'
        full_name = 'My Name'
        self.submit_form(email, full_name)

        self.assertEqual(self.User.objects.count(), 1)
        new_user = self.User.objects.get(email=email)
        self.assertEqual(new_user.full_name, full_name)

        self.assertEqual(ApplicationSubmission.objects.count(), 1)
        self.assertEqual(ApplicationSubmission.objects.first().user, new_user)

    def test_associated_if_not_new(self):
        email = 'test@test.com'
        full_name = 'My Name'

        self.submit_form(email, full_name)
        self.submit_form(email, full_name)

        self.assertEqual(self.User.objects.count(), 1)

        user = self.User.objects.get(email=email)
        self.assertEqual(ApplicationSubmission.objects.count(), 2)
        self.assertEqual(ApplicationSubmission.objects.first().user, user)

    def test_associated_if_logged_in(self):
        email = 'test@test.com'
        full_name = 'My Name'
        user = self.User.objects.create(email=email, full_name=full_name)

        self.assertEqual(self.User.objects.count(), 1)

        self.submit_form(email=email, name=full_name, user=user)

        self.assertEqual(self.User.objects.count(), 1)

        self.assertEqual(ApplicationSubmission.objects.count(), 1)
        self.assertEqual(ApplicationSubmission.objects.first().user, user)

    # This will need to be updated when we hide user information contextually
    def test_errors_if_blank_user_data_even_if_logged_in(self):
        email = 'test@test.com'
        full_name = 'My Name'
        user = self.User.objects.create(email=email, full_name=full_name)

        self.assertEqual(self.User.objects.count(), 1)

        response = self.submit_form(email='', name='', user=user)
        self.assertContains(response, 'This field is required')

        self.assertEqual(self.User.objects.count(), 1)

        self.assertEqual(ApplicationSubmission.objects.count(), 0)
