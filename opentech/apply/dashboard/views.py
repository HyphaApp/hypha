from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from .tables import DashboardTable, SubmissionFilter, SubmissionFilterAndSearch


class DashboardView(SingleTableMixin, FilterView):
    template_name = 'dashboard/dashboard.html'
    table_class = DashboardTable

    filterset_class = SubmissionFilter

    def get_context_data(self, **kwargs):
        active_filters = self.filterset.data
        return super().get_context_data(active_filters=active_filters, **kwargs)


class SearchView(SingleTableMixin, FilterView):
    template_name = 'dashboard/search.html'
    table_class = DashboardTable

    filterset_class = SubmissionFilterAndSearch

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')

        # We have more data than just 'query'
        active_filters = len(self.filterset.data) > 1

        return super().get_context_data(
            search_term=search_term,
            active_filters=active_filters,
            **kwargs,
        )
