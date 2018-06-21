from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory, ApplicationRevisionFactory
from opentech.apply.users.tests.factories import UserFactory
from opentech.apply.utils.tests import BaseViewTestCase


class TestApplicantDashboard(BaseViewTestCase):
    user_factory = UserFactory
    url_name = 'dashboard:{}'
    base_view_name = 'dashboard'

    def test_can_access_dashboard_with_active(self):
        application = ApplicationSubmissionFactory(user=self.user, form_data__title='Improve the internet')
        response = self.get_page()
        self.assertContains(response, application.title)
        self.assertNotContains(response, 'Submission history')

    def test_can_has_draft_titles_on_dashboard(self):
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
        ApplicationSubmissionFactory(user=self.user, draft_proposal=True)
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
