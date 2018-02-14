from datetime import date, timedelta
import itertools

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from wagtail.wagtailcore.models import Site

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.workflow import SingleStage

from .factories import (
    ApplicationFormFactory,
    CustomFormFieldsFactory,
    FundTypeFactory,
    LabFactory,
    LabFormFactory,
    RoundFactory,
    RoundFormFactory,
)


def days_from_today(days):
    return date.today() + timedelta(days=days)


class TestFundModel(TestCase):
    def setUp(self):
        self.fund = FundTypeFactory(parent=None)

    def test_can_access_workflow_class(self):
        self.assertEqual(self.fund.workflow_name, 'single')
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


class TestRoundModelDates(TestCase):
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


class TestRoundModelWorkflowAndForms(TestCase):
    def setUp(self):
        self.fund = FundTypeFactory(parent=None)

        self.round = RoundFactory.build()
        self.round.parent_page = self.fund

        self.fund.add_child(instance=self.round)

    def test_workflow_is_copied_to_new_rounds(self):
        self.round.save()
        self.assertEqual(self.round.workflow_name, self.fund.workflow_name)

    def test_forms_are_copied_to_new_rounds(self):
        self.round.save()
        for round_form, fund_form in itertools.zip_longest(self.round.forms.all(), self.fund.forms.all()):
            self.assertEqual(round_form, fund_form)

    def test_can_change_round_form_not_fund(self):
        self.round.save()
        # We are no longer creating a round
        del self.round.parent_page
        form = self.round.forms.first().form
        # Not ideal, would prefer better way to create the stream values
        new_field = CustomFormFieldsFactory.generate(None, {'0__email__': ''})
        form.form_fields = new_field
        form.save()
        for round_form, fund_form in itertools.zip_longest(self.round.forms.all(), self.fund.forms.all()):
            self.assertNotEqual(round_form, fund_form)


class TestFormSubmission(TestCase):
    def setUp(self):
        self.site = Site.objects.first()
        self.User = get_user_model()

        self.email = 'test@test.com'
        self.name = 'My Name'

        self.request_factory = RequestFactory()
        # set up application form with minimal requirement for creating user
        application_form = {
            'form_fields__0__email__': '',
            'form_fields__1__full_name__': '',
        }
        form = ApplicationFormFactory(**application_form)
        fund = FundTypeFactory()

        self.site.root_page = fund
        self.site.save()

        self.round_page = RoundFactory(parent=fund)
        RoundFormFactory(round=self.round_page, form=form)
        self.lab_page = LabFactory()
        LabFormFactory(lab=self.lab_page, form=form)

    def submit_form(self, page=None, email=None, name=None, user=AnonymousUser()):
        if email is None:
            email = self.email
        if name is None:
            name = self.name

        page = page or self.round_page
        fields = page.get_form_fields()
        data = {k: v for k, v in zip(fields, [email, name])}

        request = self.request_factory.post('', data)
        request.user = user
        request.site = self.site

        try:
            return page.get_parent().serve(request)
        except AttributeError:
            return page.serve(request)

    def test_can_submit_if_new(self):
        self.submit_form()

        self.assertEqual(self.User.objects.count(), 1)
        new_user = self.User.objects.get(email=self.email)
        self.assertEqual(new_user.get_full_name(), self.name)

        self.assertEqual(ApplicationSubmission.objects.count(), 1)
        self.assertEqual(ApplicationSubmission.objects.first().user, new_user)

    def test_associated_if_not_new(self):
        self.submit_form()
        self.submit_form()

        self.assertEqual(self.User.objects.count(), 1)

        user = self.User.objects.get(email=self.email)
        self.assertEqual(ApplicationSubmission.objects.count(), 2)
        self.assertEqual(ApplicationSubmission.objects.first().user, user)

    def test_associated_if_another_user_exists(self):
        self.submit_form()
        # Someone else submits a form
        self.submit_form(email='another@email.com')

        self.assertEqual(self.User.objects.count(), 2)

        first_user, second_user = self.User.objects.all()
        self.assertEqual(ApplicationSubmission.objects.count(), 2)
        self.assertEqual(ApplicationSubmission.objects.first().user, first_user)
        self.assertEqual(ApplicationSubmission.objects.last().user, second_user)

    def test_associated_if_logged_in(self):
        user, _ = self.User.objects.get_or_create(email=self.email, defaults={'full_name': self.name})

        self.assertEqual(self.User.objects.count(), 1)

        self.submit_form(email=self.email, name=self.name, user=user)

        self.assertEqual(self.User.objects.count(), 1)

        self.assertEqual(ApplicationSubmission.objects.count(), 1)
        self.assertEqual(ApplicationSubmission.objects.first().user, user)

    # This will need to be updated when we hide user information contextually
    def test_errors_if_blank_user_data_even_if_logged_in(self):
        user, _ = self.User.objects.get_or_create(email=self.email, defaults={'full_name': self.name})

        self.assertEqual(self.User.objects.count(), 1)

        response = self.submit_form(email='', name='', user=user)
        self.assertContains(response, 'This field is required')

        self.assertEqual(self.User.objects.count(), 1)

        self.assertEqual(ApplicationSubmission.objects.count(), 0)

    def test_email_sent_to_user_on_submission_fund(self):
        self.submit_form()
        # "Thank you for your submission" and "Account Creation"
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to[0], self.email)

    def test_email_sent_to_user_on_submission_lab(self):
        self.submit_form(page=self.lab_page)
        # "Thank you for your submission" and "Account Creation"
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to[0], self.email)
