import django_filters as filters
import django_tables2 as tables

from wagtail.wagtailcore.models import Page

from opentech.apply.funds.models import ApplicationSubmission, Round
from opentech.apply.funds.workflow import status_options
from .widgets import Select2MultiCheckboxesWidget


class DashboardTable(tables.Table):
    submit_time = tables.DateColumn(verbose_name="Submitted")
    status_name = tables.Column(verbose_name="Status")
    stage = tables.Column(verbose_name="Type")
    page = tables.Column(verbose_name="Fund")

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'status_name', 'stage', 'page', 'round', 'submit_time', 'user')
        template = "dashboard/tables/table.html"

    def render_user(self, value):
        return value.get_full_name()


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


class Select2CheckboxWidgetMixin:
    def __init__(self, *args, **kwargs):
        label = kwargs.get('label')
        kwargs.setdefault('widget', Select2MultiCheckboxesWidget(attrs={'data-placeholder': label}))
        super().__init__(*args, **kwargs)


class Select2MultipleChoiceFilter(Select2CheckboxWidgetMixin, filters.MultipleChoiceFilter):
    pass


class Select2ModelMultipleChoiceFilter(Select2MultipleChoiceFilter, filters.ModelMultipleChoiceFilter):
    pass


class SubmissionFilter(filters.FilterSet):
    round = Select2ModelMultipleChoiceFilter(queryset=get_used_rounds, label="Rounds")
    page = Select2ModelMultipleChoiceFilter(queryset=get_used_funds, label='Funds')
    status = Select2MultipleChoiceFilter(name='status__contains', choices=status_options, label='Status')

    class Meta:
        model = ApplicationSubmission
        fields = ('page', 'round', 'status')
