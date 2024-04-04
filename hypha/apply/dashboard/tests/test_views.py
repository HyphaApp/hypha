from hypha.apply.funds.tests.factories import (
    ApplicationRevisionFactory,
    ApplicationSubmissionFactory,
    InvitedToProposalFactory,
)
from hypha.apply.projects.models.payment import (
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    RESUBMITTED,
    SUBMITTED,
)
from hypha.apply.projects.models.project import INTERNAL_APPROVAL
from hypha.apply.projects.tests.factories import InvoiceFactory, ProjectFactory
from hypha.apply.review.tests.factories import ReviewFactory, ReviewOpinionFactory
from hypha.apply.users.tests.factories import (
    AdminFactory,
    ApplicantFactory,
    ReviewerFactory,
    StaffFactory,
    StaffWithoutWagtailAdminAccessFactory,
    StaffWithWagtailAdminAccessFactory,
)
from hypha.apply.utils.testing.tests import BaseViewTestCase


class TestApplicantDashboard(BaseViewTestCase):
    user_factory = ApplicantFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"
    partial_submissions_view_name = "applicant_submissions"

    def test_can_access_submissions_partials_with_active(self):
        application = ApplicationSubmissionFactory(
            user=self.user, form_data__title="Improve the internet"
        )
        response = self.get_page(view_name=self.partial_submissions_view_name)
        self.assertContains(response, application.title)
        self.assertNotContains(response, "Submission history")

    def test_can_have_draft_titles_on_submissions_partials(self):
        submission = ApplicationSubmissionFactory(user=self.user)
        draft_revision = ApplicationRevisionFactory(submission=submission)
        submission.draft_revision = draft_revision
        submission.save()
        response = self.get_page(view_name=self.partial_submissions_view_name)
        self.assertNotContains(response, submission.title)
        self.assertContains(response, submission.from_draft().title)
        self.assertNotContains(response, "Submission history")

    def test_can_not_access_other_users_active(self):
        application = ApplicationSubmissionFactory(form_data__title="Ruin the internet")
        response = self.get_page()
        self.assertNotContains(response, application.title)
        self.assertNotContains(response, "Submission history")

    def test_submissions_partials_gets_invite_if_invited_to_proposal(self):
        InvitedToProposalFactory(user=self.user, draft=True)
        response = self.get_page(view_name=self.partial_submissions_view_name)
        self.assertContains(response, "Start your ")

    def test_submissions_partials_no_invite_if_can_edit(self):
        ApplicationSubmissionFactory(
            user=self.user, status="concept_more_info", workflow_stages=2
        )
        response = self.get_page(view_name=self.partial_submissions_view_name)
        self.assertNotContains(response, "Start your ")
        self.assertContains(response, "Edit", 1)

    def test_no_edit_if_in_review(self):
        ApplicationSubmissionFactory(user=self.user, status="internal_review")
        response = self.get_page()
        self.assertNotContains(response, "Edit")
        self.assertNotContains(response, "Submission history")


class TestStaffDashboard(BaseViewTestCase):
    user_factory = StaffFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_cannot_see_submission_in_determination_when_not_lead(self):
        ApplicationSubmissionFactory(
            status="concept_review_discussion",
            workflow_stages=2,
            form_data__title="Reviewr",
        )
        response = self.get_page()
        self.assertNotContains(response, "Reviewr")

    def test_waiting_for_review_with_count(self):
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[self.user]
        )
        response = self.get_page()
        self.assertContains(response, "Submissions waiting for your review")
        self.assertContains(response, submission.title)
        self.assertEqual(response.context["awaiting_reviews"]["count"], 1)

    def test_waiting_for_review_after_agreement_is_empty(self):
        staff = StaffFactory()
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[staff, self.user]
        )
        review = ReviewFactory(
            submission=submission,
            author__reviewer=staff,
            author__staff=True,
            recommendation_yes=True,
        )
        ReviewOpinionFactory(
            review=review, author__reviewer=self.user, opinion_agree=True
        )
        response = self.get_page()
        self.assertContains(response, "Submissions waiting for your review")
        self.assertContains(response, "Nice! You're all caught up.")
        self.assertEqual(response.context["awaiting_reviews"]["count"], 0)

    def test_active_invoices_with_no_project(self):
        response = self.get_page()
        self.assertNotContains(response, "Active Invoices")

    def test_doesnt_show_active_invoices_with_none(self):
        ProjectFactory(lead=self.user)

        response = self.get_page()
        self.assertNotContains(response, "Active Invoices")

    def test_doest_show_active_invoices_when_paid_or_declined(self):
        project = ProjectFactory(lead=self.user)
        InvoiceFactory(project=project, status=PAID)
        InvoiceFactory(project=project, status=DECLINED)

        response = self.get_page()
        self.assertNotContains(response, "Active Invoices")

    def test_active_invoices_with_invoices_in_correct_state(self):
        project = ProjectFactory(lead=self.user)
        InvoiceFactory(project=project, status=SUBMITTED)
        InvoiceFactory(project=project, status=CHANGES_REQUESTED_BY_STAFF)
        InvoiceFactory(project=project, status=RESUBMITTED)

        response = self.get_page()
        self.assertContains(response, "Active Invoices")

    def test_doesnt_show_active_invoices_when_not_mine(self):
        project = ProjectFactory()
        InvoiceFactory(project=project, status=SUBMITTED)
        InvoiceFactory(project=project, status=CHANGES_REQUESTED_BY_STAFF)
        InvoiceFactory(project=project, status=RESUBMITTED)

        response = self.get_page()
        self.assertNotContains(response, "Active Invoices")

    def test_unassigned_staff_cant_see_projects_awaiting_review_stats_or_table(self):
        ProjectFactory(is_locked=False, status=INTERNAL_APPROVAL)

        response = self.get_page()
        self.assertNotContains(response, "Projects awaiting approval")


class TestStaffDashboardWithWagtailAdminAccess(BaseViewTestCase):
    user_factory = StaffWithWagtailAdminAccessFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_does_show_admin_button_to_staff_with_wagtail_admin_access(self):
        response = self.get_page()
        self.assertContains(response, "wagtail-admin-button")


class TestStaffDashboardWithoutWagtailAdminAccess(BaseViewTestCase):
    user_factory = StaffWithoutWagtailAdminAccessFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_doesnt_show_admin_button_to_staff_without_wagtail_admin_access(self):
        response = self.get_page()
        self.assertNotContains(response, "wagtail-admin-button")


class TestReviewerDashboard(BaseViewTestCase):
    user_factory = ReviewerFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_waiting_for_review_with_count(self):
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[self.user]
        )
        response = self.get_page()
        self.assertContains(response, "Submissions waiting for your review")
        self.assertContains(response, submission.title)
        self.assertEqual(response.context["in_review_count"], 1)

    def test_no_submissions_waiting_for_review(self):
        submission = ApplicationSubmissionFactory(
            status="external_review", workflow_stages=2, reviewers=[]
        )
        response = self.get_page()
        self.assertNotContains(response, submission.title)
        self.assertEqual(response.context["in_review_count"], 0)

    def test_submission_assigned_but_not_in_external_review_status(self):
        submission = ApplicationSubmissionFactory(
            status="concept_review_discussion", workflow_stages=2, reviewers=[self.user]
        )
        response = self.get_page()
        self.assertNotContains(response, submission.title)
        self.assertEqual(response.context["in_review_count"], 0)


class TestAdminDashboard(BaseViewTestCase):
    user_factory = AdminFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_does_show_admin_button_to_admins(self):
        response = self.get_page()
        self.assertContains(response, "wagtail-admin-button")
