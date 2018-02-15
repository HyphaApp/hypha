import django_filters as filters
import django_tables2 as tables
from django_select2.forms import Select2MultipleWidget

from wagtail.wagtailcore.models import Page

from opentech.apply.funds.models import ApplicationSubmission, Round


class DashboardTable(tables.Table):
    submit_time = tables.DateColumn(verbose_name="Submitted")
    page = tables.Column(verbose_name="Fund")

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'page', 'round', 'submit_time', 'user')
        template = "dashboard/tables/table.html"

    def render_user(self, value):
        return value.get_full_name()


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


class Select2ModelMultipleChoiceFilter(filters.ModelMultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', Select2MultipleWidget)
        super().__init__(*args, **kwargs)


class SubmissionFilter(filters.FilterSet):
    round = Select2ModelMultipleChoiceFilter(queryset=get_used_rounds)
    page = Select2ModelMultipleChoiceFilter(queryset=get_used_funds, label='Funds')

    class Meta:
        model = ApplicationSubmission
        fields = ('page', 'round',)
