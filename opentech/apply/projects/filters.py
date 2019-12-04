import django_filters as filters
from django import forms
from django.contrib.auth import get_user_model

from opentech.apply.funds.tables import (
    Select2ModelMultipleChoiceFilter,
    Select2MultipleChoiceFilter,
    get_used_funds
)

from .models import (
    PROJECT_STATUS_CHOICES,
    REQUEST_STATUS_CHOICES,
    PaymentRequest,
    Project,
    Report,
)

User = get_user_model()


def get_project_leads(request):
    return User.objects.filter(lead_projects__isnull=False).distinct()


class PaymentRequestListFilter(filters.FilterSet):
    fund = Select2ModelMultipleChoiceFilter(label='Funds', queryset=get_used_funds, field_name='project__submission__page')
    status = Select2MultipleChoiceFilter(label='Status', choices=REQUEST_STATUS_CHOICES)
    lead = Select2ModelMultipleChoiceFilter(label='Lead', queryset=get_project_leads, field_name='project__lead')

    class Meta:
        fields = ['lead', 'fund', 'status']
        model = PaymentRequest


class ProjectListFilter(filters.FilterSet):
    fund = Select2ModelMultipleChoiceFilter(label='Funds', queryset=get_used_funds)
    lead = Select2ModelMultipleChoiceFilter(label='Lead', queryset=get_project_leads)
    status = Select2MultipleChoiceFilter(label='Status', choices=PROJECT_STATUS_CHOICES)
    query = filters.CharFilter(field_name='title', lookup_expr="icontains", widget=forms.HiddenInput)

    class Meta:
        fields = ['status', 'lead', 'fund']
        model = Project


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
        label="Reporting Period",
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
