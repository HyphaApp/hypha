from django_tables2 import SingleTableView

from .tables import InvestmentTable
from .models import Investment


class InvestmentTableView(SingleTableView):
    model = Investment
    table_class = InvestmentTable
    table_pagination = {'per_page': 25}
    template_name = 'partner/investments.html'

    def get_table_kwargs(self):
        kwargs = super(InvestmentTableView, self).get_table_kwargs()
        kwargs['request'] = self.request
        return kwargs
