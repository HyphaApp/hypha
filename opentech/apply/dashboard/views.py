from django.views.generic import TemplateView

from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.tables import SubmissionsTable
from opentech.apply.utils.views import ViewDispatcher


class AdminDashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'


class ApplicantDashboardView(SingleTableView):
    template_name = 'dashboard/applicant_dashboard.html'
    model = ApplicationSubmission
    table_class = SubmissionsTable

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user).inactive()

    def get_context_data(self, **kwargs):
        my_active_submissions = self.model.objects.filter(user=self.request.user).active().current()

        return super().get_context_data(
            my_active_submissions=my_active_submissions,
            **kwargs,
        )


class DashboardView(ViewDispatcher):
    admin_view = AdminDashboardView
    applicant_view = ApplicantDashboardView
