from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.tables import SubmissionsTable, AdminSubmissionsTable
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(TemplateView):

    def get(self, request, *args, **kwargs):
        qs = ApplicationSubmission.objects.all()

        in_review = SubmissionsTable(qs.in_review_for(request.user), prefix='in-review-')
        RequestConfig(request, paginate={'per_page': 10}).configure(in_review)

        awaiting_determination = AdminSubmissionsTable(
            qs.awaiting_determination_for(request.user),
            prefix='pending-determination-'
        )
        RequestConfig(request, paginate={'per_page': 10}).configure(awaiting_determination)

        return render(request, 'dashboard/dashboard.html', {
            'in_review': in_review,
            'awaiting_determination': awaiting_determination,
        })


class ReviewerDashboardView(TemplateView):
    def get(self, request, *args, **kwargs):
        qs = ApplicationSubmission.objects.all()

        my_review_qs = qs.in_review_for(request.user)
        my_review = SubmissionsTable(my_review_qs, prefix='my-review-')
        RequestConfig(request, paginate={'per_page': 10}).configure(my_review)

        also_in_review = AdminSubmissionsTable(
            qs.in_review_for(request.user, assigned=False).exclude(id__in=my_review_qs),
            prefix='also-in-review-'
        )
        RequestConfig(request, paginate={'per_page': 10}).configure(also_in_review)

        return render(request, 'dashboard/reviewer_dashboard.html', {
            'my_review': my_review,
            'also_in_review': also_in_review,
        })


class ApplicantDashboardView(SingleTableView):
    template_name = 'dashboard/applicant_dashboard.html'
    model = ApplicationSubmission
    table_class = SubmissionsTable

    def get_queryset(self):
        return self.model.objects.filter(
            user=self.request.user
        ).inactive().current()

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
