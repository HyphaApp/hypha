from django.views.generic import TemplateView

from opentech.apply.funds.models import ApplicationSubmission


class DashboardView(TemplateView):
    template_name = 'dashboard/dashboard.html'


class ApplicantDashboardView(TemplateView):
    template_name = 'dashboard/applicant_dashboard.html'

    def get_context_data(self, **kwargs):
        my_submissions = ApplicationSubmission.objects.filter(user=self.request.user)
        my_active_submissions = my_submissions

        return super().get_context_data(
            my_submissions=my_submissions,
            my_active_submissions=my_active_submissions,
            **kwargs,
        )
