from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission, RoundsAndLabs
from opentech.apply.funds.tables import (
    ReviewerSubmissionsTable,
    SubmissionFilterAndSearch,
    SubmissionReviewerFilterAndSearch,
    SubmissionsTable,
    SummarySubmissionsTable,
    SummarySubmissionsTableWithRole,
    review_filter_for_user,
)
from opentech.apply.projects.models import Project
from opentech.apply.projects.tables import ProjectsDashboardTable
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(TemplateView):

    def get(self, request, *args, **kwargs):
        # redirect to submissions list when we use the filter to search for something
        if len(request.GET):
            query_str = '?'
            for key, value in request.GET.items():
                query_str += key + '=' + value + '&'
            return HttpResponseRedirect(reverse_lazy('funds:submissions:list') + query_str)

        qs = ApplicationSubmission.objects.all().for_table(self.request.user)

        base_query = RoundsAndLabs.objects.with_progress().active().order_by('-end_date')
        base_query = base_query.by_lead(request.user)
        open_rounds = base_query.open()[:6]
        open_query = '?round_state=open'
        closed_rounds = base_query.closed()[:6]
        closed_query = '?round_state=closed'
        rounds_title = 'Your rounds and labs'

        # Staff reviewer's current to-review submissions
        my_review_qs, my_review, display_more = self.get_my_reviews(request.user, qs)

        # Staff reviewer's reviewed submissions for 'Previous reviews' block
        filterset, my_reviewed_qs, my_reviewed, display_more_reviewed = self.get_my_reviewed(request, qs)

        # Filter for all active statuses.
        active_statuses_filter = ''.join(f'&status={status}' for status in review_filter_for_user(request.user))

        projects = self.get_my_projects(request.user)

        context = {
            'open_rounds': open_rounds,
            'open_query': open_query,
            'closed_rounds': closed_rounds,
            'closed_query': closed_query,
            'rounds_title': rounds_title,
            'my_review': my_review,
            'in_review_count': my_review_qs.count(),
            'display_more': display_more,
            'my_reviewed': my_reviewed,
            'display_more_reviewed': display_more_reviewed,
            'filter': filterset,
            'active_statuses_filter': active_statuses_filter,
            'projects': projects,
        }

        return render(request, 'dashboard/dashboard.html', context)

    def get_my_projects(self, user):
        projects = Project.objects.order_by(F('proposed_end').asc(nulls_last=True))[:10]

        if not projects:
            return

        return ProjectsDashboardTable(projects)

    def get_my_reviews(self, user, qs):
        my_review_qs = qs.in_review_for(user).order_by('-submit_time')
        my_review_table = SummarySubmissionsTableWithRole(my_review_qs[:5], prefix='my-review-')
        display_more = (my_review_qs.count() > 5)

        return my_review_qs, my_review_table, display_more

    def get_my_reviewed(self, request, qs):
        # Replicating django_filters.views.FilterView
        my_reviewed_qs = qs.reviewed_by(request.user).order_by('-submit_time')
        kwargs = {
            'data': self.request.GET or None,
            'request': self.request,
            'queryset': my_reviewed_qs,
        }
        filterset = SubmissionFilterAndSearch(**kwargs)
        my_reviewed_qs = filterset.qs

        my_reviewed_table = SummarySubmissionsTable(my_reviewed_qs[:5], prefix='my-reviewed-')
        display_more_reviewed = (my_reviewed_qs.count() > 5)

        return filterset, my_reviewed_qs, my_reviewed_table, display_more_reviewed


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


class ApplicantDashboardView(SingleTableView):
    template_name = 'dashboard/applicant_dashboard.html'
    model = ApplicationSubmission
    table_class = SubmissionsTable

    def get_queryset(self):
        return self.model.objects.filter(
            user=self.request.user
        ).inactive().current().for_table(self.request.user)

    def get_context_data(self, **kwargs):
        my_active_submissions = self.model.objects.filter(
            user=self.request.user
        ).active().current().select_related('draft_revision')

        my_active_submissions = [
            submission.from_draft() for submission in my_active_submissions
        ]

        return super().get_context_data(
            my_active_submissions=my_active_submissions,
            **kwargs,
        )


class DashboardView(ViewDispatcher):
    admin_view = AdminDashboardView
    reviewer_view = ReviewerDashboardView
    partner_view = PartnerDashboardView
    community_view = CommunityDashboardView
    applicant_view = ApplicantDashboardView
