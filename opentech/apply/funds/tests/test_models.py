from datetime import date, timedelta
import itertools
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from wagtail.core.models import Site

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.workflow import Request
from opentech.apply.utils.testing import make_request

from .factories import (
    ApplicationSubmissionFactory,
    CustomFormFieldsFactory,
    FundTypeFactory,
    LabFactory,
    RoundFactory,
)


def days_from_today(days):
    return date.today() + timedelta(days=days)


class TestFundModel(TestCase):
    def setUp(self):
        self.fund = FundTypeFactory(parent=None)

    def test_can_access_workflow_class(self):
        self.assertEqual(self.fund.workflow_name, 'single')
        self.assertEqual(self.fund.workflow, Request)

    def test_no_open_rounds(self):
        self.assertIsNone(self.fund.open_round)

    def test_open_ended_round(self):
        open_round = RoundFactory(start_date=date.today(), end_date=None, parent=self.fund)
        self.assertEqual(self.fund.open_round, open_round)

    def test_normal_round(self):
        open_round = RoundFactory(parent=self.fund, now=True)
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
        open_round = RoundFactory(parent=self.fund, now=True)
        next_round_start = open_round.end_date + timedelta(days=1)
        RoundFactory(start_date=next_round_start, end_date=None, parent=self.fund)
        self.assertEqual(self.fund.open_round, open_round)

    def test_can_not_be_open_with_draft_round(self):
        new_round = RoundFactory(parent=self.fund)
        new_round.live = False
        new_round.save()
        self.assertEqual(self.fund.open_round, None)

    def test_no_round_exists(self):
        self.assertIsNone(self.fund.next_deadline())


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

        # Must create lead, adding child complains about "built" user with no id
        lead = RoundFactory.lead.get_factory()(**RoundFactory.lead.defaults)
        self.round = RoundFactory.build(lead=lead, parent=None)

        # Assign parent_page like the init does
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

        fund = FundTypeFactory()

        self.site.root_page = fund
        self.site.save()

        self.round_page = RoundFactory(parent=fund, now=True)
        self.lab_page = LabFactory(lead=self.round_page.lead)

    def submit_form(self, page=None, email=None, name=None, user=AnonymousUser()):
        if email is None:
            email = self.email
        if name is None:
            name = self.name

        page = page or self.round_page
        fields = page.get_form_fields()
        data = {k: v for k, v in zip(fields, ['project', 0, email, name])}
        request = make_request(user, data, method='post', site=self.site)

        try:
            response = page.get_parent().serve(request)
        except AttributeError:
            response = page.serve(request)

        self.assertNotContains(response, 'There where some errors with your form')
        return response

    def test_workflow_and_status_assigned(self):
        self.submit_form()
        submission = ApplicationSubmission.objects.first()
        first_phase = list(self.round_page.workflow.keys())[0]
        self.assertEqual(submission.workflow, self.round_page.workflow)
        self.assertEqual(submission.status, first_phase)

    def test_workflow_and_status_assigned_lab(self):
        self.submit_form(page=self.lab_page)
        submission = ApplicationSubmission.objects.first()
        first_phase = list(self.lab_page.workflow.keys())[0]
        self.assertEqual(submission.workflow, self.lab_page.workflow)
        self.assertEqual(submission.status, first_phase)

    def test_can_submit_if_new(self):
        self.submit_form()

        # Lead + applicant
        self.assertEqual(self.User.objects.count(), 2)
        new_user = self.User.objects.get(email=self.email)
        self.assertEqual(new_user.get_full_name(), self.name)

        self.assertEqual(ApplicationSubmission.objects.count(), 1)
        self.assertEqual(ApplicationSubmission.objects.first().user, new_user)

    def test_associated_if_not_new(self):
        self.submit_form()
        self.submit_form()

        # Lead + applicant
        self.assertEqual(self.User.objects.count(), 2)

        user = self.User.objects.get(email=self.email)
        self.assertEqual(ApplicationSubmission.objects.count(), 2)
        self.assertEqual(ApplicationSubmission.objects.first().user, user)

    def test_associated_if_another_user_exists(self):
        email = 'another@email.com'
        self.submit_form()
        # Someone else submits a form
        self.submit_form(email=email)

        # Lead + 2 x applicant
        self.assertEqual(self.User.objects.count(), 3)

        first_user, second_user = self.User.objects.get(email=self.email), self.User.objects.get(email=email)
        self.assertEqual(ApplicationSubmission.objects.count(), 2)
        self.assertEqual(ApplicationSubmission.objects.first().user, first_user)
        self.assertEqual(ApplicationSubmission.objects.last().user, second_user)

    def test_associated_if_logged_in(self):
        user, _ = self.User.objects.get_or_create(email=self.email, defaults={'full_name': self.name})

        # Lead + Applicant
        self.assertEqual(self.User.objects.count(), 2)

        self.submit_form(email=self.email, name=self.name, user=user)

        # Lead + Applicant
        self.assertEqual(self.User.objects.count(), 2)

        self.assertEqual(ApplicationSubmission.objects.count(), 1)
        self.assertEqual(ApplicationSubmission.objects.first().user, user)

    # This will need to be updated when we hide user information contextually
    def test_errors_if_blank_user_data_even_if_logged_in(self):
        user, _ = self.User.objects.get_or_create(email=self.email, defaults={'full_name': self.name})

        # Lead + applicant
        self.assertEqual(self.User.objects.count(), 2)

        response = self.submit_form(email='', name='', user=user)
        self.assertContains(response, 'This field is required')

        # Lead + applicant
        self.assertEqual(self.User.objects.count(), 2)

        self.assertEqual(ApplicationSubmission.objects.count(), 0)

    @override_settings(SEND_MESSAGES=True)
    def test_email_sent_to_user_on_submission_fund(self):
        self.submit_form()
        # "Thank you for your submission" and "Account Creation"
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to[0], self.email)

    @override_settings(SEND_MESSAGES=True)
    def test_email_sent_to_user_on_submission_lab(self):
        self.submit_form(page=self.lab_page)
        # "Thank you for your submission" and "Account Creation"
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to[0], self.email)


class TestApplicationSubmission(TestCase):
    def make_submission(self, **kwargs):
        return ApplicationSubmissionFactory(**kwargs)

    def refresh(self, instance):
        return instance.__class__.objects.get(id=instance.id)

    def test_can_get_required_block_names(self):
        email = 'test@test.com'
        submission = self.make_submission(user__email=email)
        self.assertEqual(submission.email, email)

    def test_can_get_ordered_qs(self):
        # Emails are created sequentially
        submission_a = self.make_submission()
        submission_b = self.make_submission(round=submission_a.round)
        submissions = [submission_a, submission_b]
        self.assertEqual(
            list(ApplicationSubmission.objects.order_by('id')),
            submissions,
        )

    def test_can_get_reverse_ordered_qs(self):
        submission_a = self.make_submission()
        submission_b = self.make_submission(round=submission_a.round)
        submissions = [submission_b, submission_a]
        self.assertEqual(
            list(ApplicationSubmission.objects.order_by('-id')),
            submissions,
        )

    def test_richtext_in_char_is_removed_for_search(self):
        text = 'I am text'
        rich_text = f'<b>{text}</b>'
        submission = self.make_submission(form_data__char=rich_text)
        self.assertNotIn(rich_text, submission.search_data)
        self.assertIn(text, submission.search_data)

    def test_richtext_is_removed_for_search(self):
        text = 'I am text'
        rich_text = f'<b>{text}</b>'
        submission = self.make_submission(form_data__rich_text=rich_text)
        self.assertNotIn(rich_text, submission.search_data)
        self.assertIn(text, submission.search_data)

    def test_choices_added_for_search(self):
        choices = ['blah', 'foo']
        submission = self.make_submission(form_fields__radios__choices=choices, form_data__radios=['blah'])
        self.assertIn('blah', submission.search_data)

    def test_number_not_in_search(self):
        value = 12345
        submission = self.make_submission(form_data__number=value)
        self.assertNotIn(str(value), submission.search_data)

    def test_file_gets_uploaded(self):
        filename = 'file_name.png'
        submission = self.make_submission(form_data__image__filename=filename)
        save_path = os.path.join(settings.MEDIA_ROOT, submission.save_path(filename))
        self.assertTrue(os.path.isfile(save_path))

    def test_create_revision_on_create(self):
        submission = ApplicationSubmissionFactory()
        self.assertEqual(submission.revisions.count(), 1)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)

    def test_create_revision_on_data_change(self):
        submission = ApplicationSubmissionFactory()
        new_data = {'title': 'My Awesome Title'}
        submission.form_data = new_data
        submission.create_revision()
        submission = self.refresh(submission)
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.live_revision.form_data, new_data)

    def test_dont_create_revision_on_data_same(self):
        submission = ApplicationSubmissionFactory()
        submission.create_revision()
        self.assertEqual(submission.revisions.count(), 1)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)

    def test_can_get_draft_data(self):
        submission = ApplicationSubmissionFactory()
        title = 'My new title'
        submission.form_data = {'title': title}
        submission.create_revision(draft=True)
        self.assertEqual(submission.revisions.count(), 2)

        draft_submission = submission.from_draft()
        self.assertDictEqual(draft_submission.form_data, submission.form_data)
        self.assertEqual(draft_submission.title, title)
        self.assertTrue(draft_submission.is_draft, True)

        with self.assertRaises(ValueError):
            draft_submission.save()

        submission = self.refresh(submission)
        self.assertNotEqual(submission.title, title)

    def test_draft_updated(self):
        submission = ApplicationSubmissionFactory()
        title = 'My new title'
        submission.form_data = {'title': title}
        submission.create_revision(draft=True)
        self.assertEqual(submission.revisions.count(), 2)

        title = 'My even newer title'
        submission.form_data = {'title': title}
        submission.create_revision(draft=True)
        self.assertEqual(submission.revisions.count(), 2)
