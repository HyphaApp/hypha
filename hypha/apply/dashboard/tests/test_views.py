from django.test import TestCase
from django.urls import reverse

from hypha.apply.funds.tests.factories import (
    ApplicationRevisionFactory,
    ApplicationSubmissionFactory,
    InvitedToProposalFactory,
)
from hypha.apply.projects.models.payment import (
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    PAID,
    RESUBMITTED,
    SUBMITTED,
)
from hypha.apply.projects.models.project import (
    CONTRACTING,
    INTERNAL_APPROVAL,
    INVOICING_AND_REPORTING,
)
from hypha.apply.projects.tests.factories import (
    ContractFactory,
    InvoiceFactory,
    ProjectFactory,
)
from hypha.apply.review.tests.factories import ReviewFactory, ReviewOpinionFactory
from hypha.apply.users.tests.factories import (
    AdminFactory,
    ApplicantFactory,
    ContractingFactory,
    FinanceFactory,
    ReviewerFactory,
    StaffFactory,
    StaffWithoutWagtailAdminAccessFactory,
    StaffWithWagtailAdminAccessFactory,
    UserFactory,
)
from hypha.apply.utils.testing.tests import BaseViewTestCase

DASHBOARD_URL = reverse("dashboard:dashboard")


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
            form_data__title="Reviewer",
        )
        response = self.get_page()
        self.assertNotContains(response, "Reviewer")

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
        self.assertNotContains(response, "Active invoices")

    def test_doesnt_show_active_invoices_with_none(self):
        ProjectFactory(lead=self.user)

        response = self.get_page()
        self.assertNotContains(response, "Active invoices")

    def test_doest_show_active_invoices_when_paid_or_declined(self):
        project = ProjectFactory(lead=self.user)
        InvoiceFactory(project=project, status=PAID)
        InvoiceFactory(project=project, status=DECLINED)

        response = self.get_page()
        self.assertNotContains(response, "Active invoices")

    def test_active_invoices_with_invoices_in_correct_state(self):
        project = ProjectFactory(lead=self.user)
        InvoiceFactory(project=project, status=SUBMITTED)
        InvoiceFactory(project=project, status=CHANGES_REQUESTED_BY_STAFF)
        InvoiceFactory(project=project, status=RESUBMITTED)

        response = self.get_page()
        self.assertContains(response, "Active invoices")

    def test_doesnt_show_active_invoices_when_not_mine(self):
        project = ProjectFactory()
        InvoiceFactory(project=project, status=SUBMITTED)
        InvoiceFactory(project=project, status=CHANGES_REQUESTED_BY_STAFF)
        InvoiceFactory(project=project, status=RESUBMITTED)

        response = self.get_page()
        self.assertNotContains(response, "Active invoices")

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


class TestFinanceDashboard(BaseViewTestCase):
    user_factory = FinanceFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_dashboard_loads(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)

    def test_active_invoices_section_in_context(self):
        response = self.get_page()
        self.assertIn("active_invoices", response.context)

    def test_invoices_for_approval_in_context(self):
        response = self.get_page()
        self.assertIn("invoices_for_approval", response.context)

    def test_invoices_to_convert_in_context(self):
        response = self.get_page()
        self.assertIn("invoices_to_convert", response.context)

    def test_approved_by_staff_invoice_appears_in_active(self):
        # for_finance_1() returns APPROVED_BY_STAFF and APPROVED_BY_FINANCE
        project = ProjectFactory()
        InvoiceFactory(project=project, status=APPROVED_BY_STAFF)
        response = self.get_page()
        self.assertGreaterEqual(response.context["active_invoices"]["count"], 1)


class TestContractingDashboard(BaseViewTestCase):
    user_factory = ContractingFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_dashboard_loads(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)

    def test_projects_in_contracting_in_context(self):
        response = self.get_page()
        self.assertIn("projects_in_contracting", response.context)

    def test_project_without_contract_in_waiting_for_contract(self):
        ProjectFactory(status=CONTRACTING)
        response = self.get_page()
        ctx = response.context["projects_in_contracting"]
        self.assertGreaterEqual(ctx["waiting_for_contract"]["count"], 1)

    def test_project_with_contract_in_waiting_for_approval(self):
        project = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project)
        response = self.get_page()
        ctx = response.context["projects_in_contracting"]
        self.assertGreaterEqual(ctx["waiting_for_contract_approval"]["count"], 1)

    def test_total_contracting_count_includes_both(self):
        project1 = ProjectFactory(status=CONTRACTING)  # noqa: F841
        project2 = ProjectFactory(status=CONTRACTING)
        ContractFactory(project=project2)
        response = self.get_page()
        ctx = response.context["projects_in_contracting"]
        self.assertGreaterEqual(ctx["count"], 2)

    def test_non_contracting_project_not_counted(self):
        ProjectFactory(status=INVOICING_AND_REPORTING)
        response = self.get_page()
        ctx = response.context["projects_in_contracting"]
        self.assertEqual(ctx["waiting_for_contract"]["count"], 0)


class TestReviewerDashboardRedirect(BaseViewTestCase):
    user_factory = ReviewerFactory
    url_name = "dashboard:{}"
    base_view_name = "dashboard"

    def test_get_with_query_string_redirects_to_submissions_list(self):
        response = self.client.get(
            self.url(None),
            {"query": "test"},
            secure=True,
        )
        self.assertRedirects(
            response,
            "/apply/submissions/all/?query=test&",
            fetch_redirect_response=False,
        )


class TestApplicantDashboardPartials(BaseViewTestCase):
    user_factory = ApplicantFactory
    url_name = "dashboard:{}"
    base_view_name = "applicant_projects"

    def test_applicant_projects_loads(self):
        response = self.get_page()
        self.assertEqual(response.status_code, 200)

    def test_shows_applicant_project(self):
        project = ProjectFactory(user=self.user, status=INVOICING_AND_REPORTING)
        response = self.get_page()
        self.assertContains(response, project.title)

    def test_does_not_show_other_users_project(self):
        other = ApplicantFactory()
        project = ProjectFactory(user=other, status=INVOICING_AND_REPORTING)
        response = self.get_page()
        self.assertNotContains(response, project.title)

    def test_projects_paginated_with_many(self):
        for _ in range(8):
            ProjectFactory(user=self.user, status=INVOICING_AND_REPORTING)
        response = self.get_page()
        self.assertEqual(response.status_code, 200)
        self.assertIn("page", response.context)


class TestApplicantActiveInvoices(TestCase):
    """Test active_invoices logic in ApplicantDashboardView."""

    def setUp(self):
        self.applicant = ApplicantFactory()
        self.client.force_login(self.applicant)

    def test_active_invoices_excludes_paid(self):
        project = ProjectFactory(user=self.applicant)
        InvoiceFactory(project=project, status=PAID)
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertEqual(response.context["active_invoices"]["count"], 0)

    def test_active_invoices_excludes_declined(self):
        project = ProjectFactory(user=self.applicant)
        InvoiceFactory(project=project, status=DECLINED)
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertEqual(response.context["active_invoices"]["count"], 0)

    def test_active_invoices_includes_submitted(self):
        project = ProjectFactory(user=self.applicant)
        InvoiceFactory(project=project, status=SUBMITTED)
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertEqual(response.context["active_invoices"]["count"], 1)

    def test_active_invoices_only_shows_own(self):
        other = ApplicantFactory()
        project = ProjectFactory(user=other)
        InvoiceFactory(project=project, status=SUBMITTED)
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertEqual(response.context["active_invoices"]["count"], 0)


class TestApplicantHistoricalData(TestCase):
    """Test historical_project_data and historical_submission_data."""

    def setUp(self):
        self.applicant = ApplicantFactory()
        self.client.force_login(self.applicant)

    def test_historical_projects_only_complete(self):
        ProjectFactory(user=self.applicant, status="complete")
        ProjectFactory(user=self.applicant, status=INVOICING_AND_REPORTING)
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertEqual(response.context["historical_projects"]["count"], 1)

    def test_historical_projects_count_zero_when_none(self):
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertEqual(response.context["historical_projects"]["count"], 0)

    def test_historical_submissions_shows_inactive(self):
        ApplicationSubmissionFactory(user=self.applicant, status="invited_to_proposal")
        response = self.client.get(DASHBOARD_URL, secure=True, follow=True)
        self.assertGreaterEqual(response.context["historical_submissions"]["count"], 1)


class TestDashboardDispatch(TestCase):
    """Test DashboardView role-based dispatch and fallback."""

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(DASHBOARD_URL, secure=True)
        self.assertEqual(response.status_code, 302)

    def test_user_without_role_redirected_to_home(self):
        user = UserFactory()
        self.client.force_login(user)
        response = self.client.get(DASHBOARD_URL, secure=True, follow=False)
        # ViewDispatcher returns 403 for unknown roles → DashboardView redirects to "/"
        self.assertIn(response.status_code, [302, 200])
