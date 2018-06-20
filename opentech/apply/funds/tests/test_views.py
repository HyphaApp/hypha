from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory, StaffFactory
from opentech.apply.utils.tests import BaseViewTestCase


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

    def test_can_progress_stage(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, lead=self.user)
        response = self.post_page(submission, {'form-submitted-progress_form': '', 'action': 'invited_to_proposal'})

        # Cant use refresh from DB with FSM
        submission_original = self.refresh(submission)
        submission_next = submission_original.next

        self.assertRedirects(response, self.url(submission_next))
        self.assertEqual(submission_original.status, 'invited_to_proposal')
        self.assertEqual(submission_next.status, 'draft_proposal')

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

    def test_create_revisions_on_submit(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2)
        old_data = submission.form_data
        self.post_page(submission, {'proposal_discussion': True}, 'edit')
        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'proposal_discussion')
        self.assertEqual(submission.revisions.count(), 2)
        self.asswerEqual(submission.revisions.first().form_data, old_data)
        self.assertEqual(submission.form_data, {})

    def test_dont_update_live_revision_on_save(self):
        submission = ApplicationSubmissionFactory(status='draft_proposal', workflow_stages=2)
        old_data = submission.form_data
        self.post_page(submission, {'save': True}, 'edit')
        submission = self.refresh(submission)
        self.assertEqual(submission.status, 'draft_proposal')
        self.assertEqual(submission.revisions.count(), 2)
        self.asswerEqual(submission.revisions.first().form_data, old_data)
        self.assertEqual(submission.form_data, {})
