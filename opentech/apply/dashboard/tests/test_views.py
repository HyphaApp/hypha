from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    ApplicationRevisionFactory,
    InvitedToProposalFactory,
)
from opentech.apply.users.tests.factories import UserFactory, ReviewerFactory, StaffFactory
from opentech.apply.utils.testing.tests import BaseViewTestCase


class TestApplicantDashboard(BaseViewTestCase):
    user_factory = UserFactory
    url_name = 'dashboard:{}'
    base_view_name = 'dashboard'

    def test_can_access_dashboard_with_active(self):
        application = ApplicationSubmissionFactory(user=self.user, form_data__title='Improve the internet')
        response = self.get_page()
        self.assertContains(response, application.title)
        self.assertNotContains(response, 'Submission history')

    def test_can_have_draft_titles_on_dashboard(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        draft_revision = ApplicationRevisionFactory(submission=submission)
        submission.draft_revision = draft_revision
        submission.save()
        response = self.get_page()
        self.assertNotContains(response, submission.title)
        self.assertContains(response, submission.from_draft().title)
        self.assertNotContains(response, 'Submission history')

    def test_can_not_access_other_users_active(self):
        application = ApplicationSubmissionFactory(form_data__title='Ruin the internet')
        response = self.get_page()
        self.assertNotContains(response, application.title)
        self.assertNotContains(response, 'Submission history')

    def test_gets_invite_if_invited_to_proposal(self):
        InvitedToProposalFactory(user=self.user, draft=True)
        response = self.get_page()
        self.assertContains(response, 'Start your ')

    def test_no_invite_if_can_edit(self):
        ApplicationSubmissionFactory(user=self.user, status='concept_more_info', workflow_stages=2)
        response = self.get_page()
        self.assertNotContains(response, 'Start your ')
        self.assertContains(response, 'Edit', 1)

    def test_no_edit_if_in_review(self):
        ApplicationSubmissionFactory(user=self.user, status='internal_review')
        response = self.get_page()
        self.assertNotContains(response, 'Edit')
        self.assertNotContains(response, 'Submission history')


class TestStaffDashboard(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = 'dashboard:{}'
    base_view_name = 'dashboard'

    def test_cannot_see_submission_in_determination_when_not_lead(self):
        ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, form_data__title='Reviewr')
        response = self.get_page()
        self.assertNotContains(response, 'Reviewr')

    def test_waiting_for_review_with_count(self):
        submission = ApplicationSubmissionFactory(status='external_review', workflow_stages=2, reviewers=[self.user])
        response = self.get_page()
        self.assertContains(response, 'Waiting for your review')
        self.assertContains(response, submission.title)
        self.assertEquals(response.context['in_review_count'], 1)


class TestReviewerDashboard(BaseViewTestCase):
    user_factory = ReviewerFactory
    url_name = 'dashboard:{}'
    base_view_name = 'dashboard'

    def test_waiting_for_review_with_count(self):
        submission = ApplicationSubmissionFactory(status='external_review', workflow_stages=2, reviewers=[self.user])
        response = self.get_page()
        self.assertContains(response, 'Waiting for your review')
        self.assertContains(response, submission.title)
        self.assertEquals(response.context['in_review_count'], 1)

    def test_no_submissions_waiting_for_review(self):
        submission = ApplicationSubmissionFactory(status='external_review', workflow_stages=2, reviewers=[])
        response = self.get_page()
        self.assertNotContains(response, submission.title)
        self.assertEquals(response.context['in_review_count'], 0)

    def test_submission_assigned_but_not_in_external_review_status(self):
        submission = ApplicationSubmissionFactory(status='concept_review_discussion', workflow_stages=2, reviewers=[self.user])
        response = self.get_page()
        self.assertNotContains(response, submission.title)
        self.assertEquals(response.context['in_review_count'], 0)
