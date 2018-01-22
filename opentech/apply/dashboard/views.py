from django.views.generic import ListView

from opentech.apply.funds.models import ApplicationSubmission


class DashboardView(ListView):
    model = ApplicationSubmission
    template_name = 'dashboard/dashboard.html'
