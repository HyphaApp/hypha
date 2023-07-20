import django_filters as filters
import django_tables2 as tables
from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.tables import Select2MultipleChoiceFilter

from .models import Investment, InvestmentCategorySettings, PartnerPage


class YearMultipleChoiceFilter(Select2MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        years = Investment.objects.order_by('-year').values_list('year', flat=True).distinct()
        choices = [(year, str(year)) for year in years]
        super().__init__(
            *args,
            field_name='year',
            choices=choices,
            label=_('Years'),
            **kwargs,
        )

    def has_any(self, first, second):
        return any(item in second for item in first)

    def get_filter_predicate(self, v):
        return {f'{ self.field_name }': v}


class InvestmentFilter(filters.FilterSet):
    PAGE_CHOICES = (
        (25, '25'),
        (50, '50'),
        (100, '100'),
    )

    AMOUNT_COMMITTED_CHOICES = (
        ('0_250k', '0 > 250k'),
        ('250k_1m', '250k > 1m'),
        ('1m+', '1m+'),
    )

    amount_committed = Select2MultipleChoiceFilter(
        choices=AMOUNT_COMMITTED_CHOICES,
        label=_('Amount Committed ({currency})').format(currency=settings.CURRENCY_SYMBOL.strip()),
        method='filter_amount_committed'
    )
    partner__status = Select2MultipleChoiceFilter(
        choices=PartnerPage.STATUS, label=_('Status')
    )
    per_page = filters.ChoiceFilter(
        choices=PAGE_CHOICES,
        empty_label=_('Items per page'),
        label=_('Per page'),
        method='per_page_handler'
    )

    class Meta:
        model = Investment
        fields = ('year', 'amount_committed')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['year'] = YearMultipleChoiceFilter()

    def filter_amount_committed(self, queryset, name, value):
        query = Q()
        for v in value:
            if v == '0_250k':
                query |= Q(amount_committed__gte=0, amount_committed__lt=250000)
            if v == '250k_1m':
                query |= Q(amount_committed__gte=250000, amount_committed__lt=1000000)
            if v == '1m+':
                query |= Q(amount_committed__gte=1000000)
        return queryset.filter(query)

    def per_page_handler(self, queryset, name, value):
        # Pagination is already implemented in view. We only need to add per_page query parameter.
        return queryset


class InvestmentFilterAndSearch(InvestmentFilter):
    query = filters.CharFilter(field_name='partner__title', lookup_expr='icontains', widget=forms.HiddenInput)


def make_row_class(record):
    css_class = 'all-investments-table__parent'
    return css_class


class InvestmentTable(tables.Table):
    """Table for listing investments."""
    partner = tables.Column(verbose_name=_('Partner'), linkify=True, attrs={'td': {'class': 'js-title title'}})
    year = tables.Column(verbose_name=_('Year'))
    status = tables.Column(accessor='partner__status', verbose_name=_('Status'))
    amount_committed = tables.Column(verbose_name=_('Amount Committed'))
    description = tables.Column(visible=False)

    class Meta:
        model = Investment
        order_by = ('-updated_at',)
        fields = ('partner', 'year', 'status', 'amount_committed')
        template_name = 'partner/table.html'
        row_attrs = {
            'class': make_row_class,
            'data-record-id': lambda record: record.id,
        }
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
        super().__init__(data, *args, **kwargs, extra_columns=extra_columns)

    def render_amount_committed(self, value):
        return f'{int(value):,}'
