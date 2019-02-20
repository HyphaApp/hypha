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
)
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

        return render(request, 'dashboard/dashboard.html', {
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
        })

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

        context = {
            'my_review': my_review,
            'in_review_count': my_review_qs.count(),
            'display_more': display_more,
            'my_reviewed': my_reviewed,
            'display_more_reviewed': display_more_reviewed,
            'filter': filterset,
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

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        search_term = self.request.GET.get('query')
        kwargs.update(
            search_term=search_term,
        )

        return super().get_context_data(**kwargs)


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
    applicant_view = ApplicantDashboardView
