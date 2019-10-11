from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django_tables2.views import MultiTableMixin

from opentech.apply.funds.models import ApplicationSubmission, RoundsAndLabs
from opentech.apply.funds.tables import (
    ReviewerSubmissionsTable,
    SubmissionFilterAndSearch,
    SubmissionReviewerFilterAndSearch,
    SubmissionsTable,
    SummarySubmissionsTable,
    SummarySubmissionsTableWithRole,
    review_filter_for_user
)
from opentech.apply.projects.filters import ProjectListFilter
from opentech.apply.projects.models import (
    PaymentRequest,
    Project
)
from opentech.apply.projects.tables import (
    PaymentRequestsDashboardTable,
    ProjectsDashboardTable
)
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        submissions = ApplicationSubmission.objects.all().for_table(self.request.user)

        extra_context = {
            'active_payment_requests': self.get_my_active_payment_requests(self.request.user),
            'awaiting_reviews': self.get_my_awaiting_reviews(self.request.user, submissions),
            'my_reviewed': self.get_my_reviewed(self.request, submissions),
            'projects': self.get_my_projects(self.request),
            'projects_to_approve': self.get_my_projects_to_approve(self.request.user),
            'rounds': self.get_rounds(self.request.user)
        }
        current_context = super().get_context_data(**kwargs)
        return {**current_context, **extra_context}

    def get_my_active_payment_requests(self, user):
        payment_requests = PaymentRequest.objects.filter(
            project__lead=user,
        ).in_progress()

        return {
            'count': payment_requests.count(),
            'table': PaymentRequestsDashboardTable(payment_requests),
        }

    def get_my_projects(self, request):
        projects = Project.objects.filter(lead=request.user).for_table()

        filterset = ProjectListFilter(data=request.GET or None, request=request, queryset=projects)

        limit = 10

        return {
            'count': projects.count(),
            'filterset': filterset,
            'table': ProjectsDashboardTable(projects[:limit]),
            'display_more': projects.count() > limit,
            'url': reverse('apply:projects:all'),
        }

    def get_my_projects_to_approve(self, user):
        if not user.is_approver:
            return {
                'count': None,
                'table': None,
            }

        to_approve = Project.objects.in_approval().for_table()

        return {
            'count': to_approve.count(),
            'table': ProjectsDashboardTable(data=to_approve),
        }

    def get_my_awaiting_reviews(self, user, qs):
        """Staff reviewer's current to-review submissions."""
        qs = qs.in_review_for(user).order_by('-submit_time')
        count = qs.count()

        limit = 5
        return {
            'active_statuses_filter': ''.join(f'&status={status}' for status in review_filter_for_user(user)),
            'count': count,
            'display_more': count > limit,
            'table': SummarySubmissionsTableWithRole(qs[:limit], prefix='my-review-'),
        }

    def get_my_reviewed(self, request, qs):
        """Staff reviewer's reviewed submissions for 'Previous reviews' block"""
        qs = qs.reviewed_by(request.user).order_by('-submit_time')

        filterset = SubmissionFilterAndSearch(data=request.GET or None, request=request, queryset=qs)

        limit = 5
        return {
            'filterset': filterset,
            'table': SummarySubmissionsTable(qs[:limit], prefix='my-reviewed-'),
            'display_more': qs.count() > limit,
            'url': reverse('funds:submissions:list'),
        }

    def get_rounds(self, user):
        qs = (RoundsAndLabs.objects.with_progress()
                                   .active()
                                   .order_by('-end_date')
                                   .by_lead(user))
        return {
            'closed': qs.closed()[:6],
            'open': qs.open()[:6],
        }


class ReviewerDashboardView(TemplateView):

    def get(self, request, *args, **kwargs):
        # redirect to submissions list when we use the filter to search for something
        if len(request.GET):
            query_str = '?'
            for key, value in request.GET.items():
                query_str += key + '=' + value + '&'
            return HttpResponseRedirect(reverse_lazy('funds:submissions:list') + query_str)

        qs = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Reviewer's current to-review submissions
        my_review_qs, my_review, display_more = self.get_my_reviews(request.user, qs)

        # Reviewer's reviewed submissions and filters for 'Previous reviews' block
        filterset, my_reviewed_qs, my_reviewed, display_more_reviewed = self.get_my_reviewed(request, qs)

        # Filter for all active statuses.
        active_statuses_filter = ''.join(f'&status={status}' for status in review_filter_for_user(request.user))

        # Applications by reviewer
        my_submissions, my_inactive_submissions = self.get_my_submissions(request, qs)

        context = {
            'my_review': my_review,
            'in_review_count': my_review_qs.count(),
            'display_more': display_more,
            'my_reviewed': my_reviewed,
            'display_more_reviewed': display_more_reviewed,
            'filter': filterset,
            'active_statuses_filter': active_statuses_filter,
            'my_submissions': my_submissions,
            'my_inactive_submissions': my_inactive_submissions,
        }

        return render(request, 'dashboard/reviewer_dashboard.html', context)

    def get_my_reviews(self, user, qs):
        my_review_qs = qs.in_review_for(user).order_by('-submit_time')
        my_review_table = ReviewerSubmissionsTable(my_review_qs[:5], prefix='my-review-')
        display_more = (my_review_qs.count() > 5)

        return my_review_qs, my_review_table, display_more

    def get_my_reviewed(self, request, qs):
        # Replicating django_filters.views.FilterView
        my_reviewed_qs = qs.reviewed_by(request.user).order_by('-submit_time')

        kwargs = {
            'data': request.GET or None,
            'request': request,
            'queryset': my_reviewed_qs,
        }
        filterset = SubmissionReviewerFilterAndSearch(**kwargs)
        my_reviewed_qs = filterset.qs

        my_reviewed_table = ReviewerSubmissionsTable(my_reviewed_qs[:5], prefix='my-reviewed-')
        display_more_reviewed = (my_reviewed_qs.count() > 5)

        return filterset, my_reviewed_qs, my_reviewed_table, display_more_reviewed

    def get_my_submissions(self, request, qs):
        my_submissions = qs.filter(
            user=request.user
        ).active().current().select_related('draft_revision')
        my_submissions = [
            submission.from_draft() for submission in my_submissions
        ]

        my_inactive_submissions_qs = qs.filter(user=self.request.user).inactive().current()
        my_inactive_submissions_table = ReviewerSubmissionsTable(
            my_inactive_submissions_qs, prefix='my-submissions-'
        )
        return my_submissions, my_inactive_submissions_table

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('query')
        kwargs.update(
            search_term=search_term,
        )

        return super().get_context_data(**kwargs)


class PartnerDashboardView(TemplateView):
    template_name = 'dashboard/partner_dashboard.html'

    def get_partner_submissions(self, user, qs):
        partner_submissions_qs = qs.partner_for(user).order_by('-submit_time')
        partner_submissions_table = ReviewerSubmissionsTable(partner_submissions_qs, prefix='my-partnered-')

        return partner_submissions_qs, partner_submissions_table

    def get_my_reviewed(self, request, qs):
        my_reviewed_qs = qs.reviewed_by(request.user).order_by('-submit_time')
        my_reviewed_table = ReviewerSubmissionsTable(my_reviewed_qs, prefix='my-reviewed-')

        return my_reviewed_qs, my_reviewed_table

    def get_my_submissions(self, request, qs):
        my_submissions = qs.filter(
            user=request.user
        ).active().current().select_related('draft_revision')
        my_submissions = [
            submission.from_draft() for submission in my_submissions
        ]

        my_inactive_submissions_qs = qs.filter(user=self.request.user).inactive().current()
        my_inactive_submissions_table = ReviewerSubmissionsTable(
            my_inactive_submissions_qs, prefix='my-submissions-'
        )
        return my_submissions, my_inactive_submissions_table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in which user added as partner
        partner_submissions_qs, partner_submissions = self.get_partner_submissions(self.request.user, qs)

        # Partner's reviewed submissions
        my_reviewed_qs, my_reviewed = self.get_my_reviewed(self.request, qs)

        # Applications by partner
        my_submissions, my_inactive_submissions = self.get_my_submissions(self.request, qs)

        context.update({
            'partner_submissions': partner_submissions,
            'partner_submissions_count': partner_submissions_qs.count(),
            'my_reviewed': my_reviewed,
            'my_submissions': my_submissions,
            'my_inactive_submissions': my_inactive_submissions,
        })

        return context


class CommunityDashboardView(TemplateView):
    template_name = 'dashboard/community_dashboard.html'

    def get_my_community_review(self, user, qs):
        my_community_review_qs = qs.in_community_review(user).order_by('-submit_time')
        my_community_review_table = ReviewerSubmissionsTable(my_community_review_qs, prefix='my-community-review-')

        return my_community_review_qs, my_community_review_table

    def get_my_reviewed(self, request, qs):
        my_reviewed_qs = qs.reviewed_by(request.user).order_by('-submit_time')
        my_reviewed_table = ReviewerSubmissionsTable(my_reviewed_qs, prefix='my-reviewed-')

        return my_reviewed_qs, my_reviewed_table

    def get_my_submissions(self, request, qs):
        my_submissions = qs.filter(
            user=request.user
        ).active().current().select_related('draft_revision')
        my_submissions = [
            submission.from_draft() for submission in my_submissions
        ]

        my_inactive_submissions_qs = qs.filter(user=self.request.user).inactive().current()
        my_inactive_submissions_table = ReviewerSubmissionsTable(
            my_inactive_submissions_qs, prefix='my-submissions-'
        )
        return my_submissions, my_inactive_submissions_table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Submissions in community review phase
        my_community_review_qs, my_community_review = self.get_my_community_review(self.request.user, qs)

        # Partner's reviewed submissions
        my_reviewed_qs, my_reviewed = self.get_my_reviewed(self.request, qs)

        # Applications by partner
        my_submissions, my_inactive_submissions = self.get_my_submissions(self.request, qs)

        context.update({
            'my_community_review': my_community_review,
            'my_community_review_count': my_community_review_qs.count(),
            'my_reviewed': my_reviewed,
            'my_submissions': my_submissions,
            'my_inactive_submissions': my_inactive_submissions,
        })

        return context


class ApplicantDashboardView(MultiTableMixin, TemplateView):
    tables = [
        ProjectsDashboardTable,
        SubmissionsTable,
        ProjectsDashboardTable,
    ]
    template_name = 'dashboard/applicant_dashboard.html'

    def get_context_data(self, **kwargs):
        active_submissions = list(self.get_active_submissions(self.request.user))

        context = super().get_context_data(**kwargs)
        context['my_active_submissions'] = active_submissions
        return context

    def get_active_project_data(self, user):
        return Project.objects.filter(user=user).in_progress().for_table()

    def get_active_submissions(self, user):
        active_subs = ApplicationSubmission.objects.filter(
            user=user,
        ) .active().current().select_related('draft_revision')

        for submission in active_subs:
            yield submission.from_draft()

    def get_historical_project_data(self, user):
        return Project.objects.filter(user=user).complete().for_table()

    def get_historical_submission_data(self, user):
        return ApplicationSubmission.objects.filter(
            user=user,
        ).inactive().current().for_table(user)

    def get_tables_data(self):
        return [
            self.get_active_project_data(self.request.user),
            self.get_historical_submission_data(self.request.user),
            self.get_historical_project_data(self.request.user),
        ]


class DashboardView(ViewDispatcher):
    admin_view = AdminDashboardView
    reviewer_view = ReviewerDashboardView
    partner_view = PartnerDashboardView
    community_view = CommunityDashboardView
    applicant_view = ApplicantDashboardView
