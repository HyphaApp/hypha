from django_tables2 import SingleTableView

from .models import Investment
from .tables import InvestmentTable


class InvestmentTableView(SingleTableView):
    model = Investment
    table_class = InvestmentTable
    table_pagination = {'per_page': 25}
    template_name = 'partner/investments.html'
