from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from django_tables2.views import SingleTableView

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.tables import SubmissionsTable
from opentech.apply.users.groups import STAFF_GROUP_NAME


class AdminDashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'


class ApplicantDashboardView(SingleTableView):
    template_name = 'dashboard/applicant_dashboard.html'
    model = ApplicationSubmission
    table_class = SubmissionsTable

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        my_active_submissions = self.object_list.active()

        return super().get_context_data(
            my_active_submissions=my_active_submissions,
            **kwargs,
        )


@method_decorator(login_required, name='dispatch')
class DashboardView(View):
    def dispatch(self, request):
        if request.user.groups.filter(name=STAFF_GROUP_NAME).exists():
            view = AdminDashboardView
        else:
            view = ApplicantDashboardView

        return view.as_view()(request)
