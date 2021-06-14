from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django_tables2.views import MultiTableMixin

from hypha.apply.funds.models import ApplicationSubmission, RoundsAndLabs
from hypha.apply.funds.tables import (
    ReviewerSubmissionsTable,
    SubmissionFilterAndSearch,
    SubmissionReviewerFilterAndSearch,
    SubmissionsTable,
    SummarySubmissionsTable,
    SummarySubmissionsTableWithRole,
    review_filter_for_user,
)
from hypha.apply.projects.filters import ProjectListFilter
from hypha.apply.projects.models import PaymentRequest, Project, vendor
from hypha.apply.projects.tables import (
    PaymentRequestsDashboardTable,
    ProjectsDashboardTable,
)
from hypha.apply.utils.views import ViewDispatcher


class MySubmissionContextMixin:
    def get_context_data(self, **kwargs):
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)
        my_submissions = submissions.filter(
            user=self.request.user
        ).active().current().select_related('draft_revision')
        my_submissions = [
            submission.from_draft() for submission in my_submissions
        ]

        my_inactive_submissions = submissions.filter(user=self.request.user).inactive().current()
        my_inactive_submissions_table = ReviewerSubmissionsTable(
            my_inactive_submissions, prefix='my-submissions-'
        )

        return super().get_context_data(
            my_submissions=my_submissions,
            my_inactive_submissions=my_inactive_submissions_table,
            **kwargs,
        )


class MyFlaggedMixin:
    def my_flagged(self, submissions):
        submissions = submissions.flagged_by(self.request.user).order_by('-submit_time')
        row_attrs = dict({'data-flag-type': 'user'}, **SummarySubmissionsTable._meta.row_attrs)

        limit = 5
        return {
            'table': SummarySubmissionsTable(submissions[:limit], prefix='my-flagged-', attrs={'class': 'all-submissions-table flagged-table'}, row_attrs=row_attrs),
            'display_more': submissions.count() > limit,
        }


class AdminDashboardView(MyFlaggedMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        context.update({
            'active_payment_requests': self.active_payment_requests(),
            'awaiting_reviews': self.awaiting_reviews(submissions),
            'my_reviewed': self.my_reviewed(submissions),
            'projects': self.projects(),
            'projects_to_approve': self.projects_to_approve(),
            'rounds': self.rounds(),
            'my_flagged': self.my_flagged(submissions),
        })

        return context

    def awaiting_reviews(self, submissions):
        submissions = submissions.in_review_for(self.request.user).order_by('-submit_time')
        count = submissions.count()

        limit = 5
        return {
            'active_statuses_filter': ''.join(f'&status={status}' for status in review_filter_for_user(self.request.user)),
            'count': count,
            'display_more': count > limit,
            'table': SummarySubmissionsTableWithRole(submissions[:limit], prefix='my-review-'),
        }

    def active_payment_requests(self):
        payment_requests = PaymentRequest.objects.filter(
            project__lead=self.request.user,
        ).in_progress()

        return {
            'count': payment_requests.count(),
            'table': PaymentRequestsDashboardTable(payment_requests),
        }

    def projects(self):
        projects = Project.objects.filter(lead=self.request.user).for_table()

        filterset = ProjectListFilter(
            data=self.request.GET or None, request=self.request, queryset=projects)

        limit = 10

        return {
            'count': projects.count(),
            'filterset': filterset,
            'table': ProjectsDashboardTable(projects[:limit]),
            'display_more': projects.count() > limit,
            'url': reverse('apply:projects:all'),
        }

    def projects_to_approve(self):
        if not self.request.user.is_approver:
            return {
                'count': None,
                'table': None,
            }

        to_approve = Project.objects.in_approval().for_table()

        return {
            'count': to_approve.count(),
            'table': ProjectsDashboardTable(data=to_approve),
        }

    def my_reviewed(self, submissions):
        """Staff reviewer's reviewed submissions for 'Previous reviews' block"""
        submissions = submissions.reviewed_by(self.request.user).order_by('-submit_time')

        limit = 5
        return {
            'filterset': SubmissionFilterAndSearch(
                data=self.request.GET or None, request=self.request, queryset=submissions),
            'table': SummarySubmissionsTableWithRole(submissions[:limit], prefix='my-review-'),
            'display_more': submissions.count() > limit,
            'url': reverse('funds:submissions:list'),
        }

    def rounds(self):
        limit = 6
        rounds = RoundsAndLabs.objects.with_progress().active().order_by('-end_date').by_lead(
            self.request.user)
        return {
            'closed': rounds.closed()[:limit],
            'open': rounds.open()[:limit],
        }


class FinanceDashboardView(MyFlaggedMixin, TemplateView):
    template_name = 'dashboard/finance_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'active_payment_requests': self.active_payment_requests(),
        })

        return context

    def active_payment_requests(self):
        payment_requests = PaymentRequest.objects.in_progress()

        return {
            'count': payment_requests.count(),
            'table': PaymentRequestsDashboardTable(payment_requests),
        }


class ReviewerDashboardView(MyFlaggedMixin, MySubmissionContextMixin, TemplateView):
    template_name = 'dashboard/reviewer_dashboard.html'

    def get(self, request, *args, **kwargs):
        # redirect to submissions list when we use the filter to search for something
        if len(request.GET):
            query_str = '?'
            for key, value in request.GET.items():
                query_str += key + '=' + value + '&'
            return HttpResponseRedirect(reverse_lazy('funds:submissions:list') + query_str)

        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        context.update({
            'awaiting_reviews': self.awaiting_reviews(submissions),
            'my_reviewed': self.my_reviewed(submissions),
            'my_flagged': self.my_flagged(submissions),
        })

        return context

    def awaiting_reviews(self, submissions):
        submissions = submissions.in_review_for(self.request.user).order_by('-submit_time')
        count = submissions.count()

        limit = 5
        return {
            'active_statuses_filter': ''.join(f'&status={status}' for status in review_filter_for_user(self.request.user)),
            'count': count,
            'display_more': count > limit,
            'table': ReviewerSubmissionsTable(submissions[:limit], prefix='my-review-'),
        }

    def my_reviewed(self, submissions):
        """Staff reviewer's reviewed submissions for 'Previous reviews' block"""
        submissions = submissions.reviewed_by(self.request.user).order_by('-submit_time')

        limit = 5
        return {
            'filterset': SubmissionReviewerFilterAndSearch(
                data=self.request.GET or None, request=self.request, queryset=submissions),
            'table': ReviewerSubmissionsTable(submissions[:limit], prefix='my-review-'),
            'display_more': submissions.count() > limit,
            'url': reverse('funds:submissions:list'),
        }


class PartnerDashboardView(MySubmissionContextMixin, TemplateView):
    template_name = 'dashboard/partner_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in which user added as partner
        partner_submissions, partner_submissions_table = self.partner_submissions(self.request.user, submissions)

        context.update({
            'partner_submissions': partner_submissions_table,
            'partner_submissions_count': partner_submissions.count(),
        })

        return context

    def partner_submissions(self, user, submissions):
        partner_submissions = submissions.partner_for(user).order_by('-submit_time')
        partner_submissions_table = SubmissionsTable(partner_submissions, prefix='my-partnered-')

        return partner_submissions, partner_submissions_table


class CommunityDashboardView(MySubmissionContextMixin, TemplateView):
    template_name = 'dashboard/community_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in community review phase
        my_community_review, my_community_review = self.my_community_review(self.request.user, submissions)

        # Partner's reviewed submissions
        my_reviewed = self.my_reviewed(self.request, submissions)

        context.update({
            'my_community_review': my_community_review,
            'my_community_review_count': my_community_review.count(),
            'my_reviewed': my_reviewed
        })

        return context

    def my_community_review(self, user, submissions):
        my_community_review = submissions.in_community_review(user).order_by('-submit_time')
        my_community_review_table = ReviewerSubmissionsTable(my_community_review, prefix='my-community-review-')

        return my_community_review, my_community_review_table

    def my_reviewed(self, request, submissions):
        return ReviewerSubmissionsTable(submissions.reviewed_by(request.user).order_by('-submit_time'), prefix='my-reviewed-')


class ApplicantDashboardView(MultiTableMixin, TemplateView):
    tables = [
        ProjectsDashboardTable,
        SubmissionsTable,
        ProjectsDashboardTable,
    ]
    template_name = 'dashboard/applicant_dashboard.html'

    def get_context_data(self, **kwargs):
        my_active_submissions = list(self.my_active_submissions(self.request.user))

        context = super().get_context_data(**kwargs)
        context['my_active_submissions'] = my_active_submissions
        return context

    def active_project_data(self, user):
        return Project.objects.filter(user=user).active().for_table()

    def my_active_submissions(self, user):
        active_subs = ApplicationSubmission.objects.filter(
            user=user,
        ) .active().current().select_related('draft_revision')

        for submission in active_subs:
            yield submission.from_draft()

    def historical_project_data(self, user):
        return Project.objects.filter(user=user).complete().for_table()

    def historical_submission_data(self, user):
        return ApplicationSubmission.objects.filter(
            user=user,
        ).inactive().current().for_table(user)

    def get_tables_data(self):
        return [
            self.active_project_data(self.request.user),
            self.historical_submission_data(self.request.user),
            self.historical_project_data(self.request.user),
        ]


class DashboardView(ViewDispatcher):
    admin_view = AdminDashboardView
    reviewer_view = ReviewerDashboardView
    partner_view = PartnerDashboardView
    community_view = CommunityDashboardView
    applicant_view = ApplicantDashboardView
    finance_view = FinanceDashboardView
