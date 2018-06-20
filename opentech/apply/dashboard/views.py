from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.tables import SubmissionsTable, AdminSubmissionsTable
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(TemplateView):

    def get(self, request, *args, **kwargs):
        qs = ApplicationSubmission.objects

        in_review = SubmissionsTable(qs.in_review_for(request.user), prefix='in-review-')
        RequestConfig(request, paginate={'per_page': 10}).configure(in_review)

        need_determination = AdminSubmissionsTable(qs.need_determination_for(request.user), prefix='need-determination-')
        RequestConfig(request, paginate={'per_page': 10}).configure(need_determination)

        return render(request, 'dashboard/dashboard.html', {
            'in_review': in_review,
            'need_determination': need_determination,
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
    applicant_view = ApplicantDashboardView

    def admin_check(self, request):
        if request.user.is_reviewer:
            return True
        return super().admin_check(request)
