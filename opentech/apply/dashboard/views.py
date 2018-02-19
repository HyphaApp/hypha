from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from opentech.apply.funds.models import ApplicationSubmission

from .tables import DashboardTable, SubmissionFilter


class DashboardView(SingleTableMixin, FilterView):
    model = ApplicationSubmission
    template_name = 'dashboard/dashboard.html'
    table_class = DashboardTable

    filterset_class = SubmissionFilter


class SubmissionDetailView(DetailView):
    model = ApplicationSubmission
