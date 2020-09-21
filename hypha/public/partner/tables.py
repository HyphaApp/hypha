import django_tables2 as tables
from django.utils.translation import gettext_lazy as _

from .models import Investment, InvestmentCategorySettings


class InvestmentTable(tables.Table):
    """Table for listing investments."""
    partner = tables.Column(verbose_name='Partner', linkify=True)
    year = tables.Column(verbose_name='Year')
    status = tables.Column(accessor='partner__status', verbose_name='Status')
    amount_committed = tables.Column(verbose_name='Amount committed (US$)')

    class Meta:
        model = Investment
        order_by = ('-updated_at',)
        fields = ('partner', 'year', 'status', 'amount_committed')
        template_name = 'partner/table.html'
        attrs = {'class': 'all-investments-table'}
        empty_text = _('No investments available')

    def __init__(self, data, extra_columns=None, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        extra_columns = extra_columns or []
        ics = InvestmentCategorySettings.for_request(self.request)
        categories = ics.categories.all()
        for category in categories:
            field_name = category.name.lower().replace(' ', '_')
            extra_columns.append(
                (field_name, tables.Column(orderable=False,))
            )
        extra_columns.append(('primary_impact_area', tables.Column(orderable=False,)))
        extra_columns.append(('geographic_focus', tables.Column(orderable=False,)))
        super().__init__(data, extra_columns=extra_columns, *args, **kwargs)

    def render_amount_committed(self, value):
        return f'{int(value):,}'
