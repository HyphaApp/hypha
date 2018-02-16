from django.contrib.postgres.search import SearchVector
from django.db.models import TextField
from django.db.models.functions import Cast
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


class SearchView(SingleTableMixin, FilterView):
    template_name = 'dashboard/search.html'
    table_class = DashboardTable

    filterset_class = SubmissionFilter

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')
        if search_term:
            # Postgres <10 doesn't support search on JSON
            # Cast to text to make searchable
            self.object_list = self.object_list.annotate(
                search=SearchVector(Cast('form_data', TextField())),
            ).filter(search=search_term)

        return super().get_context_data(search_term=search_term, **kwargs)
