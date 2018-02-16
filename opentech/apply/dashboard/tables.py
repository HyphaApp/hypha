from django.contrib.auth import get_user_model
from django.utils.text import mark_safe

import django_filters as filters
import django_tables2 as tables
from django_tables2.utils import A

from wagtail.wagtailcore.models import Page

from opentech.apply.funds.models import ApplicationSubmission, Round
from opentech.apply.funds.workflow import status_options
from .widgets import Select2MultiCheckboxesWidget


class DashboardTable(tables.Table):
    title = tables.LinkColumn('funds:submission', args=[A('pk')], orderable=True)
    submit_time = tables.DateColumn(verbose_name="Submitted")
    status_name = tables.Column(verbose_name="Status")
    stage = tables.Column(verbose_name="Type")
    page = tables.Column(verbose_name="Fund")
    status_name = tables.Column(verbose_name="Status", empty_values=[])
    lead = tables.Column(accessor='round.specific.lead', verbose_name='Lead')

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'status_name', 'stage', 'page', 'round', 'submit_time')
        sequence = ('title', 'status_name', 'stage', 'page', 'round', 'lead', 'submit_time')
        template = "dashboard/tables/table.html"

    def render_user(self, value):
        return value.get_full_name()

    def render_status_name(self, value):
        return mark_safe(f'<span>{ value }</span>')


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


def get_round_leads(request):
    User = get_user_model()
    return User.objects.filter(round__isnull=False).distinct()


class Select2CheckboxWidgetMixin:
    def __init__(self, *args, **kwargs):
        label = kwargs.get('label')
        kwargs.setdefault('widget', Select2MultiCheckboxesWidget(attrs={'data-placeholder': label}))
        super().__init__(*args, **kwargs)


class Select2MultipleChoiceFilter(Select2CheckboxWidgetMixin, filters.MultipleChoiceFilter):
    pass


class Select2ModelMultipleChoiceFilter(Select2MultipleChoiceFilter, filters.ModelMultipleChoiceFilter):
    pass


class WagtailMulitChoiceFilter(Select2ModelMultipleChoiceFilter):
    @property
    def wagtail_query(self):
        # Queries on related pages will first attempt to query through the Page object
        def is_page(relation):
            return relation.field.related_model == Page

        wagtail_path = list()
        steps = self.field_name.split('__')
        related_item = self.model
        for step in steps:
            related_item = getattr(related_item, step)
            wagtail_path.append(step)
            if is_page(related_item):
                # Traverse over the page object to get the model at the other end
                related_item = getattr(related_item.field.related_model, step).related.remote_field.model
                wagtail_path.append(step)

        return '__'.join(wagtail_path)

    def get_filter_predicate(self, v):
        return {self.wagtail_query: v}


class SubmissionFilter(filters.FilterSet):
    round = Select2ModelMultipleChoiceFilter(queryset=get_used_rounds, label='Rounds')
    funds = Select2ModelMultipleChoiceFilter(name='page', queryset=get_used_funds, label='Funds')
    status = Select2MultipleChoiceFilter(name='status__contains', choices=status_options, label='Status')
    lead = WagtailMulitChoiceFilter(name='round__lead', queryset=get_round_leads, label='Lead')

    class Meta:
        model = ApplicationSubmission
        fields = ('funds', 'round', 'status')
