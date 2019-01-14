from datetime import datetime, timedelta
import json

from opentech.apply.activity.models import Activity
from opentech.apply.determinations.tests.factories import DeterminationFactory
from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    ApplicationRevisionFactory,
    InvitedToProposalFactory,
    LabFactory,
    LabSubmissionFactory,
    RoundFactory,
    ScreeningStatusFactory,
    SealedRoundFactory,
    SealedSubmissionFactory,
)
from opentech.apply.stream_forms.testing.factories import flatten_for_form
from opentech.apply.users.tests.factories import (
    ReviewerFactory,
    StaffFactory,
    SuperUserFactory,
    UserFactory,
)
from opentech.apply.utils.testing import make_request
from opentech.apply.utils.testing.tests import BaseViewTestCase

from ..models import ApplicationRevision


def prepare_form_data(submission, **kwargs):
    data = submission.raw_data

    for field, value in kwargs.items():
        # convert named fields into  id
        field_id = submission.field(field).id
        data[field_id] = value

    address_field = submission.named_blocks['address']
    address = data.pop(address_field)
    data.update(**prepare_address(address, address_field))

    return data


def prepare_address(address, field):
    address = json.loads(address)
    address['locality'] = {
        'localityname': address.pop('localityname'),
        'administrativearea': address.pop('administrativearea'),
        'postalcode': address.pop('postalcode'),
    }
    address = flatten_for_form(address, field, number=True)
    return address


class BaseSubmissionViewTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'pk': instance.id}


class TestStaffSubmissionView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    @classmethod
    def setUpTestData(cls):
        cls.submission = ApplicationSubmissionFactory()
        super().setUpTestData()

    def __setUp__(self):
        self.refresh(self.submission)

    def test_can_view_a_submission(self):
        response = self.get_page(self.submission)
        self.assertContains(response, self.submission.title)

    def test_can_view_a_lab_submission(self):
        submission = LabSubmissionFactory()
        response = self.get_page(submission)
        self.assertContains(response, submission.title)

    def test_can_progress_phase(self):
        next_status = list(self.submission.get_actions_for_user(self.user))[0][0]
        self.post_page(self.submission, {'form-submitted-progress_form': '', 'action': next_status})

        submission = self.refresh(self.submission)
        self.assertEqual(submission.status, next_status)

    def test_redirected_to_determination(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, lead=self.user)
        response = self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        # Invited for proposal is a a determination, so this will redirect to the determination form.
        url = self.url_from_pattern('funds:submissions:determinations:form', kwargs={'submission_pk': submission.id})
        self.assertRedirects(response, f"{url}?action=invited_to_proposal")

    def test_new_form_after_progress(self):
        submission = ApplicationSubmissionFactory(status='invited_to_proposal', workflow_stages=2, lead=self.user)
        stage = submission.stage
        DeterminationFactory(submission=submission, accepted=True)

        request = make_request(self.user, method='get', site=submission.page.get_site())
        submission.progress_stage_when_possible(self.user, request)

        submission = self.refresh(submission)
        new_stage = submission.stage

        self.assertNotEqual(stage, new_stage)

        get_forms = submission.get_from_parent('get_defined_fields')
        self.assertEqual(submission.form_fields, get_forms(new_stage))
        self.assertNotEqual(submission.form_fields, get_forms(stage))

    def test_cant_progress_stage_if_not_lead(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2)
        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        submission = self.refresh(submission)

        self.assertEqual(submission.status, 'concept_review_discussion')
        self.assertIsNone(submission.next)

    def test_not_redirected_if_determination_submitted(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        DeterminationFactory(submission=submission, rejected=True, submitted=True)

        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'rejected'})

        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'rejected')

    def test_not_redirected_if_wrong_determination_selected(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        DeterminationFactory(submission=submission, accepted=True, submitted=True)

        response = self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'rejected'})
        self.assertContains(response, 'you tried to progress')

        submission = self.refresh(submission)
        self.assertNotEqual(submission.status, 'accepted')
        self.assertNotEqual(submission.status, 'rejected')

    def test_cant_access_edit_button_when_applicant_editing(self):
        submission = ApplicationSubmissionFactory(status='more_info')
        response = self.get_page(submission)
        self.assertNotContains(response, self.url(submission, 'edit', absolute=False))

    def test_can_access_edit_button(self):
        response = self.get_page(self.submission)
        self.assertContains(response, self.url(self.submission, 'edit', absolute=False))

    def test_can_access_edit(self):
        response = self.get_page(self.submission, 'edit')
        self.assertContains(response, self.submission.title)

    def test_previous_and_next_appears_on_page(self):
        proposal = InvitedToProposalFactory()
        response = self.get_page(proposal)
        self.assertContains(response, self.url(proposal.previous, absolute=False))

        response = self.get_page(proposal.previous)
        self.assertContains(response, self.url(proposal, absolute=False))

    def test_can_edit_submission(self):
        old_status = self.submission.status
        new_title = 'A new Title'
        data = prepare_form_data(self.submission, title=new_title)
        response = self.post_page(self.submission, {'submit': True, **data}, 'edit')

        url = self.url(self.submission)

        self.assertRedirects(response, url)
        submission = self.refresh(self.submission)

        # Staff edits don't affect the status
        self.assertEqual(old_status, submission.status)
        self.assertEqual(new_title, submission.title)

    def test_not_included_fields_render(self):
        submission = ApplicationSubmissionFactory(form_fields__exclude__value=True)
        response = self.get_page(submission)
        self.assertNotContains(response, 'Value')

    def test_can_screen_submission(self):
        screening_outcome = ScreeningStatusFactory()
        self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        submission = self.refresh(self.submission)
        self.assertEqual(submission.screening_status, screening_outcome)

    def test_cant_screen_submission(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        DeterminationFactory(submission=submission, rejected=True, submitted=True)
        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'rejected'})
        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'rejected')

        # Now that the submission has been rejected (final determination),
        # we cannot screen it as staff
        screening_outcome = ScreeningStatusFactory()
        response = self.post_page(submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        self.assertEqual(response.context_data['screening_form'].should_show, False)


class TestReviewersUpdateView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff = StaffFactory.create_batch(4)
        cls.reviewers = ReviewerFactory.create_batch(4)

    def post_form(self, submission, staff=list(), reviewers=list()):
        return self.post_page(submission, {
            'form-submitted-reviewer_form': '',
            'staff_reviewers': [s.id for s in staff],
            'reviewer_reviewers': [r.id for r in reviewers]
        })

    def test_lead_can_add_staff_single(self):
        submission = ApplicationSubmissionFactory(lead=self.user)

        self.post_form(submission, self.staff)

        self.assertCountEqual(submission.reviewers.all(), self.staff)

    def test_lead_can_remove_staff_single(self):
        submission = ApplicationSubmissionFactory(lead=self.user, reviewers=self.staff)
        self.assertCountEqual(submission.reviewers.all(), self.staff)

        self.post_form(submission, [])

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_lead_can_remove_some_staff(self):
        submission = ApplicationSubmissionFactory(lead=self.user, reviewers=self.staff)
        self.assertCountEqual(submission.reviewers.all(), self.staff)

        self.post_form(submission, self.staff[0:2])

        self.assertCountEqual(submission.reviewers.all(), self.staff[0:2])

    def test_lead_cant_add_reviewers_single(self):
        submission = ApplicationSubmissionFactory(lead=self.user)

        self.post_form(submission, reviewers=self.reviewers)

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_lead_can_add_staff_and_reviewers_for_proposal(self):
        submission = InvitedToProposalFactory(lead=self.user)

        self.post_form(submission, self.staff, self.reviewers)

        self.assertCountEqual(submission.reviewers.all(), self.staff + self.reviewers)

    def test_lead_can_remove_staff_and_reviewers_for_proposal(self):
        submission = InvitedToProposalFactory(lead=self.user, reviewers=self.staff + self.reviewers)
        self.assertCountEqual(submission.reviewers.all(), self.staff + self.reviewers)

        self.post_form(submission)

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_lead_can_remove_some_staff_and_reviewers_for_proposal(self):
        submission = InvitedToProposalFactory(lead=self.user, reviewers=self.staff + self.reviewers)
        self.assertCountEqual(submission.reviewers.all(), self.staff + self.reviewers)

        self.post_form(submission, self.staff[0:2], self.reviewers[0:2])

        self.assertCountEqual(submission.reviewers.all(), self.staff[0:2] + self.reviewers[0:2])

    def test_staff_can_add_staff_single(self):
        submission = ApplicationSubmissionFactory()

        self.post_form(submission, self.staff)

        self.assertCountEqual(submission.reviewers.all(), self.staff)

    def test_staff_can_remove_staff_single(self):
        submission = ApplicationSubmissionFactory(reviewers=self.staff)
        self.assertCountEqual(submission.reviewers.all(), self.staff)

        self.post_form(submission, [])

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_staff_cant_add_reviewers_proposal(self):
        submission = ApplicationSubmissionFactory()

        self.post_form(submission, reviewers=self.reviewers)

        self.assertCountEqual(submission.reviewers.all(), [])

    def test_staff_cant_remove_reviewers_proposal(self):
        submission = ApplicationSubmissionFactory(reviewers=self.reviewers)
        self.assertCountEqual(submission.reviewers.all(), self.reviewers)

        self.post_form(submission, reviewers=[])

        self.assertCountEqual(submission.reviewers.all(), self.reviewers)


class TestApplicantSubmissionView(BaseSubmissionViewTestCase):
    user_factory = UserFactory

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.submission = ApplicationSubmissionFactory(user=cls.user)
        cls.draft_proposal_submission = InvitedToProposalFactory(user=cls.user, draft=True)

    def __setUp__(self):
        self.refresh(self.submission)
        self.refresh(self.draft_proposal_submission)

    def test_can_view_own_submission(self):
        response = self.get_page(self.submission)
        self.assertContains(response, self.submission.title)

    def test_sees_latest_draft_if_it_exists(self):
        draft_revision = ApplicationRevisionFactory(submission=self.submission)
        self.submission.draft_revision = draft_revision
        self.submission.save()

        draft_submission = self.submission.from_draft()
        response = self.get_page(self.submission)

        self.assertContains(response, draft_submission.title)

    def test_cant_view_others_submission(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 403)

    def test_get_edit_link_when_editable(self):
        submission = ApplicationSubmissionFactory(user=self.user, status='more_info')
        response = self.get_page(submission)
        self.assertContains(response, 'Edit')
        self.assertContains(response, self.url(submission, 'edit', absolute=False))
        self.assertNotContains(response, 'Congratulations')

    def test_get_congratulations_draft_proposal(self):
        response = self.get_page(self.draft_proposal_submission)
        self.assertContains(response, 'Congratulations')

    def test_can_edit_own_submission(self):
        response = self.get_page(self.draft_proposal_submission, 'edit')
        self.assertContains(response, self.draft_proposal_submission.title)

    def test_can_submit_submission(self):
        old_status = self.draft_proposal_submission.status

        data = prepare_form_data(self.draft_proposal_submission, title='This is different')

        response = self.post_page(self.draft_proposal_submission, {'submit': True, **data}, 'edit')

        url = self.url_from_pattern('funds:submissions:detail', kwargs={'pk': self.draft_proposal_submission.id})

        self.assertRedirects(response, url)
        submission = self.refresh(self.draft_proposal_submission)
        self.assertNotEqual(old_status, submission.status)

    def test_gets_draft_on_edit_submission(self):
        draft_revision = ApplicationRevisionFactory(submission=self.draft_proposal_submission)
        self.draft_proposal_submission.draft_revision = draft_revision
        self.draft_proposal_submission.save()

        response = self.get_page(self.draft_proposal_submission, 'edit')
        self.assertDictEqual(response.context['object'].form_data, draft_revision.form_data)

    def test_cant_edit_submission_incorrect_state(self):
        submission = InvitedToProposalFactory(user=self.user)
        response = self.get_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)

    def test_cant_edit_other_submission(self):
        submission = InvitedToProposalFactory(draft=True)
        response = self.get_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)

    def test_cant_screen_submission(self):
        response = self.post_page(self.submission)
        self.assertNotIn('screening_form', response.context_data)


class TestRevisionsView(BaseSubmissionViewTestCase):
    user_factory = UserFactory

    def test_create_revisions_on_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        old_data = submission.form_data.copy()

        new_title = 'New title'
        new_data = prepare_form_data(submission, title=new_title)

        self.post_page(submission, {'submit': True, **new_data}, 'edit')

        submission = self.refresh(submission)

        self.assertEqual(submission.status, 'proposal_discussion')
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.revisions.last().form_data, old_data)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)
        self.assertEqual(submission.live_revision.author, self.user)
        self.assertEqual(submission.title, new_title)

    def test_dont_update_live_revision_on_save(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        old_data = submission.form_data.copy()

        new_data = prepare_form_data(submission, title='New title')

        self.post_page(submission, {'save': True, **new_data}, 'edit')

        submission = self.refresh(submission)

        self.assertEqual(submission.status, 'draft_proposal')
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertEqual(submission.draft_revision.author, self.user)
        self.assertDictEqual(submission.live_revision.form_data, old_data)

    def test_existing_draft_edit_and_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        draft_data = prepare_form_data(submission, title='A new title')

        self.post_page(submission, {'save': True, **draft_data}, 'edit')

        submission = self.refresh(submission)

        newer_title = 'Newer title'
        draft_data = prepare_form_data(submission, title=newer_title)
        self.post_page(submission, {'submit': True, **draft_data}, 'edit')

        submission = self.refresh(submission)

        self.maxDiff = None
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)

        self.assertEqual(submission.title, newer_title)


class TestRevisionCompare(BaseSubmissionViewTestCase):
    base_view_name = 'revisions:compare'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {
            'submission_pk': instance.pk,
            'to': instance.live_revision.id,
            'from': instance.revisions.last().id,
        }

    def test_renders_with_all_the_diffs(self):
        submission = ApplicationSubmissionFactory()
        new_data = ApplicationSubmissionFactory(round=submission.round, form_fields=submission.form_fields).form_data

        submission.form_data = new_data

        submission.create_revision()

        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)


class TestRevisionList(BaseSubmissionViewTestCase):
    base_view_name = 'revisions:list'
    user_factory = StaffFactory

    def get_kwargs(self, instance):
        return {'submission_pk': instance.pk}

    def test_list_doesnt_include_draft(self):
        submission = ApplicationSubmissionFactory()
        draft_revision = ApplicationRevisionFactory(submission=submission)
        submission.draft_revision = draft_revision
        submission.save()

        response = self.get_page(submission)

        self.assertNotIn(draft_revision, response.context['object_list'])

    def test_get_in_correct_order(self):
        submission = ApplicationSubmissionFactory()

        revision = ApplicationRevisionFactory(submission=submission)
        ApplicationRevision.objects.filter(id=revision.id).update(timestamp=datetime.now() - timedelta(days=1))

        revision_older = ApplicationRevisionFactory(submission=submission)
        ApplicationRevision.objects.filter(id=revision_older.id).update(timestamp=datetime.now() - timedelta(days=2))

        response = self.get_page(submission)

        self.assertSequenceEqual(
            response.context['object_list'],
            [submission.live_revision, revision, revision_older],
        )


class TestStaffSealedView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    def test_redirected_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.get_page(submission)
        url = self.url_from_pattern('funds:submissions:sealed', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)

    def test_cant_post_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.post_page(submission, {'some': 'data'}, 'sealed')
        # Because of the redirect chain the url returned is not absolute
        url = self.url_from_pattern('funds:submissions:sealed', kwargs={'pk': submission.id}, absolute=False)
        self.assertRedirects(response, url)

    def test_non_sealed_unaffected(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_non_sealed_redirected_away(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission, 'sealed')
        url = self.url_from_pattern('funds:submissions:detail', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)


class TestSuperUserSealedView(BaseSubmissionViewTestCase):
    user_factory = SuperUserFactory

    def test_redirected_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.get_page(submission)
        url = self.url_from_pattern('funds:submissions:sealed', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)

    def test_can_post_to_sealed(self):
        submission = SealedSubmissionFactory()
        response = self.post_page(submission, {}, 'sealed')
        url = self.url_from_pattern('funds:submissions:detail', kwargs={'pk': submission.id})
        self.assertRedirects(response, url)

    def test_peeking_is_logged(self):
        submission = SealedSubmissionFactory()
        self.post_page(submission, {}, 'sealed')

        self.assertTrue('peeked' in self.client.session)
        self.assertTrue(str(submission.id) in self.client.session['peeked'])
        self.assertEqual(Activity.objects.count(), 1)
        self.assertTrue('sealed' in Activity.objects.first().message)

    def test_not_asked_again(self):
        submission = SealedSubmissionFactory()

        self.post_page(submission, {}, 'sealed')

        # Now request the page again
        response = self.get_page(submission)
        self.assertEqual(response.status_code, 200)

    def test_can_view_multiple_sealed(self):
        sealed_round = SealedRoundFactory()
        first, second = SealedSubmissionFactory.create_batch(2, round=sealed_round)

        self.post_page(first, {}, 'sealed')
        self.post_page(second, {}, 'sealed')

        self.assertTrue('peeked' in self.client.session)
        self.assertTrue(str(first.id) in self.client.session['peeked'])
        self.assertTrue(str(second.id) in self.client.session['peeked'])


class ByRoundTestCase(BaseViewTestCase):
    url_name = 'apply:submissions:{}'
    base_view_name = 'by_round'

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


class TestSuperUserSubmissionView(BaseSubmissionViewTestCase):
    user_factory = SuperUserFactory

    @classmethod
    def setUpTestData(cls):
        cls.submission = ApplicationSubmissionFactory()
        super().setUpTestData()

    def __setUp__(self):
        self.refresh(self.submission)

    def test_can_screen_submission(self):
        screening_outcome = ScreeningStatusFactory()
        self.post_page(self.submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        submission = self.refresh(self.submission)
        self.assertEqual(submission.screening_status, screening_outcome)

    def test_cant_screen_submission(self):
        submission = ApplicationSubmissionFactory(lead=self.user)
        DeterminationFactory(submission=submission, rejected=True, submitted=True)
        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'rejected'})
        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'rejected')

        # Now that the submission has been rejected (final determination),
        # we can still screen it because we are super user
        screening_outcome = ScreeningStatusFactory()
        response = self.post_page(submission, {'form-submitted-screening_form': '', 'screening_status': screening_outcome.id})
        submission = self.refresh(submission)
        self.assertEqual(response.context_data['screening_form'].should_show, True)
        self.assertEqual(submission.screening_status, screening_outcome)
