import django_filters as filters
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2Widget

from hypha.apply.funds.tables import (
    Select2ModelMultipleChoiceFilter,
    Select2MultipleChoiceFilter,
    get_used_funds,
)

from .models.payment import INVOICE_STATUS_CHOICES, Invoice
from .models.project import CLOSING, IN_PROGRESS, PROJECT_STATUS_CHOICES, Project
from .models.report import Report

User = get_user_model()


def get_project_leads(request):
    return User.objects.filter(lead_projects__isnull=False).distinct()


class InvoiceListFilter(filters.FilterSet):
    fund = Select2ModelMultipleChoiceFilter(label=_('Funds'), queryset=get_used_funds, field_name='project__submission__page')
    status = Select2MultipleChoiceFilter(label=_('Status'), choices=INVOICE_STATUS_CHOICES)
    lead = Select2ModelMultipleChoiceFilter(label=_('Lead'), queryset=get_project_leads, field_name='project__lead')

    class Meta:
        fields = ['lead', 'fund', 'status']
        model = Invoice


class ProjectListFilter(filters.FilterSet):
    REPORTING_CHOICES = (
        (0, 'Up to date'),
        (1, 'Behind schedule'),
    )

    project_fund = Select2ModelMultipleChoiceFilter(field_name="submission__page", label=_('Funds'), queryset=get_used_funds)
    project_lead = Select2ModelMultipleChoiceFilter(field_name="lead", label=_('Lead'), queryset=get_project_leads)
    project_status = Select2MultipleChoiceFilter(field_name="status", label=_('Status'), choices=PROJECT_STATUS_CHOICES)
    query = filters.CharFilter(field_name='title', lookup_expr="icontains", widget=forms.HiddenInput)
    reporting = filters.ChoiceFilter(
        choices=REPORTING_CHOICES,
        method="filter_reporting",
        widget=Select2Widget(attrs={
            'data-placeholder': 'Reporting',
            'data-minimum-results-for-search': -1,
        }),
    )

    class Meta:
        fields = ['project_status', 'project_lead', 'project_fund']
        model = Project

    def filter_reporting(self, queryset, name, value):
        if value == '1':
            return queryset.filter(outstanding_reports__gt=0)
        return queryset.filter(
            Q(outstanding_reports__lt=1) | Q(outstanding_reports__isnull=True),
            status__in=(IN_PROGRESS, CLOSING),
        )


class DateRangeInputWidget(filters.widgets.SuffixedMultiWidget):
    template_name = 'application_projects/filters/widgets/date_range_input_widget.html'
    suffixes = ['after', 'before']

    def __init__(self, attrs=None):
        widgets = (forms.DateInput, forms.DateInput)
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class ReportListFilter(filters.FilterSet):
    reporting_period = filters.DateFromToRangeFilter(
        label=_('Reporting Period'),
        method="filter_reporting_period",
        widget=DateRangeInputWidget,
    )
    submitted = filters.DateFromToRangeFilter(widget=DateRangeInputWidget)

    class Meta:
        model = Report
        fields = ['submitted']

    def filter_reporting_period(self, queryset, name, value):
        after, before = value.start, value.stop
        q = {}
        if after:
            q['start__gte'] = after
        if before:
            q['end_date__lte'] = before

        return queryset.filter(**q)
