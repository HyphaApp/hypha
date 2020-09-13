import django_tables2 as tables
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from django.views.generic import ListView
from django_tables2 import SingleTableView

from .tables import InvestmentTable
from .models import Investment


class InvestmentTableView(SingleTableView):
    model = Investment
    table_class = InvestmentTable
    table_pagination = {'per_page': 5}
    template_name = 'partner/investments.html'
