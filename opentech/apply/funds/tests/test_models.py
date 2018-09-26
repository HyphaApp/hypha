from datetime import date, timedelta
import itertools
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.blocks import EmailBlock, FullNameBlock
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
        new_round.parent_page = {new_round.__class__: {new_round.title: self.fund}}

        with self.assertRaises(ValidationError):
            new_round.clean()


class TestRoundModelWorkflowAndForms(TestCase):
    def setUp(self):
        self.fund = FundTypeFactory(parent=None)

        # Must create lead, adding child complains about "built" user with no id
        lead = RoundFactory.lead.get_factory()(**RoundFactory.lead.defaults)
        self.round = RoundFactory.build(lead=lead, parent=None)

        # Assign parent_page like the init does
        self.round.parent_page = {self.round.__class__: {self.round.title: self.fund}}
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
        new_field = CustomFormFieldsFactory.generate(None, {})
        form.form_fields = new_field
        form.save()
        for round_form, fund_form in itertools.zip_longest(self.round.forms.all(), self.fund.forms.all()):
            self.assertNotEqual(round_form, fund_form)


@override_settings(ROOT_URLCONF='opentech.apply.urls')
class TestFormSubmission(TestCase):
    def setUp(self):
        self.User = get_user_model()

        self.email = 'test@test.com'
        self.name = 'My Name'

        fund = FundTypeFactory()

        self.site = fund.get_site()

        self.round_page = RoundFactory(parent=fund, now=True)
        self.lab_page = LabFactory(lead=self.round_page.lead)

    def submit_form(self, page=None, email=None, name=None, user=AnonymousUser(), ignore_errors=False):
        page = page or self.round_page

        fields = page.forms.first().fields
        data = CustomFormFieldsFactory.form_response(fields)

        # Add our own data
        for field in page.forms.first().fields:
            if isinstance(field.block, EmailBlock):
                data[field.id] = self.email if email is None else email
            if isinstance(field.block, FullNameBlock):
                data[field.id] = self.name if name is None else name

        request = make_request(user, data, method='post', site=self.site)

        if page.get_parent().id != self.site.root_page.id:
            # Its a fund
            response = page.get_parent().serve(request)
        else:
            response = page.serve(request)

        if not ignore_errors:
            # Check the data we submit is correct
            self.assertNotContains(response, 'errors')
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

    def test_doesnt_mess_with_name(self):
        full_name = "I have; <a> wei'rd name"
        self.submit_form(name=full_name)
        submission = ApplicationSubmission.objects.first()
        self.assertEqual(submission.user.full_name, full_name)

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

        response = self.submit_form(email='', name='', user=user, ignore_errors=True)
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
        path = os.path.join(settings.MEDIA_ROOT, 'submission', str(submission.id))

        # Check we created the top level folder
        self.assertTrue(os.path.isdir(path))

        found_files = []
        for _, _, files in os.walk(path):
            found_files.extend(files)

        # Check we saved the file somewhere beneath it
        self.assertIn(filename, found_files)

    def test_create_revision_on_create(self):
        submission = ApplicationSubmissionFactory()
        self.assertEqual(submission.revisions.count(), 1)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)
        self.assertEqual(submission.live_revision.author, submission.user)

    def test_create_revision_on_data_change(self):
        submission = ApplicationSubmissionFactory()
        submission.form_data['title'] = 'My Awesome Title'
        new_data = submission.form_data
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
        submission.form_data['title'] = title
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
        submission.form_data['title'] = title
        submission.create_revision(draft=True)
        self.assertEqual(submission.revisions.count(), 2)

        title = 'My even newer title'
        submission.form_data['title'] = title

        submission.create_revision(draft=True)
        self.assertEqual(submission.revisions.count(), 2)


class TestSubmissionRenderMethods(TestCase):
    def test_must_include_not_included_in_answers(self):
        submission = ApplicationSubmissionFactory()
        answers = submission.render_answers()
        for name in submission.must_include:
            field = submission.field(name)
            self.assertNotIn(field.value['field_label'], answers)

    def test_normal_answers_included_in_answers(self):
        submission = ApplicationSubmissionFactory()
        answers = submission.output_answers()
        for field_name in submission.question_field_ids:
            if field_name not in submission.must_include:
                field = submission.field(field_name)
                self.assertIn(field.value['field_label'], answers)

    def test_paragraph_not_rendered_in_answers(self):
        rich_text_label = 'My rich text label!'
        submission = ApplicationSubmissionFactory(
            form_fields__text_markup__value=rich_text_label
        )
        answers = submission.render_answers()
        self.assertNotIn(rich_text_label, answers)
