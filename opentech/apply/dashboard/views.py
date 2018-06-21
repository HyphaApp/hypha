from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.tables import SubmissionsTable
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(SingleTableView):
    template_name = 'dashboard/dashboard.html'
    model = ApplicationSubmission
    table_class = SubmissionsTable

    def get_queryset(self):
        return self.model.objects.in_review_for(self.request.user)


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
