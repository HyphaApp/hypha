from datetime import datetime, timedelta
import json

from addressfield.widgets import AddressWidget
from opentech.apply.activity.models import Activity
from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    ApplicationRevisionFactory,
    LabSubmissionFactory,
    SealedRoundFactory,
    SealedSubmissionFactory,
)
from opentech.apply.users.tests.factories import UserFactory, StaffFactory, SuperUserFactory
from opentech.apply.utils.testing.tests import BaseViewTestCase

from ..models import ApplicationRevision
from .test_models import flatten_for_form


class BaseSubmissionViewTestCase(BaseViewTestCase):
    url_name = 'funds:submissions:{}'
    base_view_name = 'detail'

    def get_kwargs(self, instance):
        return {'pk': instance.id}


class TestStaffSubmissionView(BaseSubmissionViewTestCase):
    user_factory = StaffFactory

    def test_can_view_a_submission(self):
        submission = ApplicationSubmissionFactory()
        response = self.get_page(submission)
        self.assertContains(response, submission.title)

    def test_can_view_a_lab_submission(self):
        submission = LabSubmissionFactory()
        response = self.get_page(submission)
        self.assertContains(response, submission.title)

    def test_can_progress_phase(self):
        submission = ApplicationSubmissionFactory()
        next_status = list(submission.get_actions_for_user(self.user))[0][0]
        self.post_page(submission, {'form-submitted-progress_form': '', 'action': next_status})

        submission = self.refresh(submission)
        self.assertEqual(submission.status, next_status)

    def test_redirected_to_determination(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, lead=self.user)
        response = self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        # Invited for proposal is a a determination, so this will redirect to the determination form.
        url = self.url_from_pattern('funds:submissions:determinations:form', kwargs={'submission_pk': submission.id})
        self.assertRedirects(response, f"{url}?action=invited_to_proposal")

    def test_cant_progress_stage_if_not_lead(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2)
        self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        submission = self.refresh(submission)

        self.assertEqual(submission.status, 'concept_review_discussion')
        self.assertIsNone(submission.next)

    def test_cant_access_edit_button_on_applicant_submission(self):
        submission = ApplicationSubmissionFactory(status='more_info')
        response = self.get_page(submission)
        self.assertNotContains(response, self.url(submission, 'edit', absolute=False))


class TestApplicantSubmissionView(BaseSubmissionViewTestCase):
    user_factory = UserFactory

    def test_can_view_own_submission(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        response = self.get_page(submission)
        self.assertContains(response, submission.title)

    def test_sees_latest_draft_if_it_exists(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        draft_revision = ApplicationRevisionFactory(submission=submission)
        submission.draft_revision = draft_revision
        submission.save()

        draft_submission = submission.from_draft()
        response = self.get_page(submission)

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
        submission = ApplicationSubmissionFactory(user=self.user, draft_proposal=True)
        response = self.get_page(submission)
        self.assertContains(response, 'Congratulations')

    def test_can_edit_own_submission(self):
        submission = ApplicationSubmissionFactory(user=self.user, draft_proposal=True)
        response = self.get_page(submission, 'edit')
        self.assertContains(response, submission.title)

    def test_gets_draft_on_edit_submission(self):
        submission = ApplicationSubmissionFactory(user=self.user, draft_proposal=True)
        draft_revision = ApplicationRevisionFactory(submission=submission)
        submission.draft_revision = draft_revision
        submission.save()

        response = self.get_page(submission, 'edit')
        self.assertDictEqual(response.context['object'].form_data, draft_revision.form_data)

    def test_cant_edit_submission_incorrect_state(self):
        submission = ApplicationSubmissionFactory(user=self.user, workflow_stages=2)
        response = self.get_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)

    def test_cant_edit_other_submission(self):
        submission = ApplicationSubmissionFactory(draft_proposal=True)
        response = self.get_page(submission, 'edit')
        self.assertEqual(response.status_code, 403)


class TestRevisionsView(BaseSubmissionViewTestCase):
    user_factory = UserFactory

    def prepare_address(self, address, field):
        address = json.loads(address)
        address['locality'] = {
            'localityname': address.pop('localityname'),
            'administrativearea': address.pop('administrativearea'),
            'postalcode': address.pop('postalcode'),
        }
        address = flatten_for_form(address, field, number=True)
        return address


    def test_create_revisions_on_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        old_data = submission.form_data.copy()
        new_data = submission.raw_data
        new_title = 'New title'
        new_data[submission.must_include['title']] = new_title

        address_id = submission.must_include['address']

        new_data.update(**self.prepare_address(
            new_data[submission.must_include['address']],
            address_id,
        ))

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

        new_data = submission.raw_data

        address_id = submission.must_include['address']

        new_data.update(**self.prepare_address(
            new_data[submission.must_include['address']],
            address_id,
        ))

        new_data[submission.must_include['title']] = 'New title'
        self.post_page(submission, {'save': True, **new_data}, 'edit')

        submission = self.refresh(submission)

        self.assertEqual(submission.status, 'draft_proposal')
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertEqual(submission.draft_revision.author, self.user)
        self.assertDictEqual(submission.live_revision.form_data, old_data)

    def test_existing_draft_edit_and_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2, user=self.user)
        draft_data = submission.raw_data.copy()

        address_id = submission.must_include['address']

        draft_data.update(**self.prepare_address(
            draft_data[submission.must_include['address']],
            address_id,
        ))

        draft_data[submission.must_include['title']] = 'New title'

        self.post_page(submission, {'save': True, **draft_data}, 'edit')

        submission = self.refresh(submission)

        new_title = 'Newer title'
        draft_data[submission.must_include['title']] = new_title
        self.post_page(submission, {'submit': True, **draft_data}, 'edit')

        submission = self.refresh(submission)

        self.maxDiff = None
        self.assertEqual(submission.revisions.count(), 2)
        self.assertDictEqual(submission.draft_revision.form_data, submission.from_draft().form_data)
        self.assertDictEqual(submission.live_revision.form_data, submission.form_data)

        self.assertEqual(submission.title, new_title)


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
