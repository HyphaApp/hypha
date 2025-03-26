import django_filters as filters
from django import forms
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.tables import (
    MultipleChoiceFilter,
)

from .models import Report


class DateRangeInputWidget(filters.widgets.SuffixedMultiWidget):
    template_name = "application_projects/filters/widgets/date_range_input_widget.html"
    suffixes = ["after", "before"]

    def __init__(self, attrs=None):
        widgets = (forms.DateInput, forms.DateInput)
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]


class ReportingFilter(filters.FilterSet):
    current_report_status = MultipleChoiceFilter(
        label=_("Status"),
        choices=[
            ("Not started", "Not started"),
            ("In progress", "In progress"),
            ("Submitted", "Submitted"),
        ],
    )


class ReportListFilter(filters.FilterSet):
    reporting_period = filters.DateFromToRangeFilter(
        label=_("Reporting Period"),
        method="filter_reporting_period",
        widget=DateRangeInputWidget,
    )
    submitted = filters.DateFromToRangeFilter(widget=DateRangeInputWidget)

    class Meta:
        model = Report
        fields = ["submitted"]

    def filter_reporting_period(self, queryset, name, value):
        after, before = value.start, value.stop
        q = {}
        if after:
            q["start__gte"] = after
        if before:
            q["end_date__lte"] = before

        return queryset.filter(**q)
