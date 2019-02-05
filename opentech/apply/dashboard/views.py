from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission, RoundsAndLabs
from opentech.apply.funds.tables import (
    AdminSubmissionsTable,
    ReviewerSubmissionsTable,
    SubmissionReviewerFilterAndSearch,
    SubmissionsTable,
)
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(TemplateView):

    def get(self, request, *args, **kwargs):
        qs = ApplicationSubmission.objects.all().for_table(self.request.user)

        in_review = SubmissionsTable(qs.in_review_for(request.user), prefix='in-review-')
        RequestConfig(request, paginate={'per_page': 10}).configure(in_review)
        base_query = RoundsAndLabs.objects.with_progress().active().order_by('-end_date')
        base_query = base_query.by_lead(request.user)
        open_rounds = base_query.open()[:6]
        open_query = '?round_state=open'
        closed_rounds = base_query.closed()[:6]
        closed_query = '?round_state=closed'
        rounds_title = 'Your rounds and labs'

        return render(request, 'dashboard/dashboard.html', {
            'in_review': in_review,
            'open_rounds': open_rounds,
            'open_query': open_query,
            'closed_rounds': closed_rounds,
            'closed_query': closed_query,
            'rounds_title': rounds_title,
        })


class ReviewerDashboardView(TemplateView):

    def get(self, request, *args, **kwargs):
        qs = ApplicationSubmission.objects.all().for_table(self.request.user)

        # Reviewer's current to-review submissions
        my_review_qs = qs.in_review_for(request.user).order_by('-submit_time')
        my_review = ReviewerSubmissionsTable(my_review_qs[:5], prefix='my-review-')
        display_more = (my_review_qs.count() > 5)
        context = {
            'my_review': my_review,
            'in_review_count': my_review_qs.count(),
            'display_more': display_more,
        }

        # Reviewer's reviewed submissions for 'Previous reviews' block
        # Replicating django_filters.views.FilterView
        my_reviewed_qs = qs.reviewed_by(request.user).order_by('-submit_time')
        kwargs = {
            'data': self.request.GET or None,
            'request': self.request,
        }
        kwargs.update({
            'queryset': my_reviewed_qs,
        })
        self.filterset = SubmissionReviewerFilterAndSearch(**kwargs)
        my_reviewed_qs = self.filterset.qs

        my_reviewed = ReviewerSubmissionsTable(my_reviewed_qs[:5], prefix='my-reviewed-')
        display_more_reviewed = (my_reviewed_qs.count() > 5)

        context.update({
            'my_reviewed': my_reviewed,
            'display_more_reviewed': display_more_reviewed,
            'filter': self.filterset,
        })

        return render(request, 'dashboard/reviewer_dashboard.html', context)

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
