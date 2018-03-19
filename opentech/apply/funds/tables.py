from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import mark_safe

import django_filters as filters
import django_tables2 as tables
from django_tables2.utils import A

from wagtail.core.models import Page

from opentech.apply.funds.models import ApplicationSubmission, Round
from opentech.apply.funds.workflow import status_options
from .widgets import Select2MultiCheckboxesWidget


def make_row_class(record):
    css_class = '' if record.active else 'is-inactive'
    css_class += ' child' if record.next else ' parent'
    return css_class


class SubmissionsTable(tables.Table):
    """Base table for listing submissions, do not include admin data to this table"""
    title = tables.LinkColumn('funds:submission', args=[A('pk')], orderable=True)
    submit_time = tables.DateColumn(verbose_name="Submitted")
    status_name = tables.Column(verbose_name="Status")
    stage = tables.Column(verbose_name="Type", order_by=('status',))
    page = tables.Column(verbose_name="Fund")
    comments = tables.Column(accessor='activities.comments.all', verbose_name="Comments")

    class Meta:
        model = ApplicationSubmission
        order_by = ('-submit_time',)
        fields = ('title', 'status_name', 'stage', 'page', 'round', 'submit_time')
        sequence = fields + ('comments',)
        template = 'funds/tables/table.html'
        row_attrs = {
            'class': make_row_class
        }

    def render_user(self, value):
        return value.get_full_name()

    def render_status_name(self, value):
        return mark_safe(f'<span>{ value }</span>')

    def render_comments(self, value):
        request = self.context['request']
        return str(value.visible_to(request.user).count())

    def order_status_name(self, qs, desc):
        return qs.step_order(desc), True


class AdminSubmissionsTable(SubmissionsTable):
    """Adds admin only columns to the submissions table"""
    lead = tables.Column(order_by=('lead.full_name',))

    class Meta(SubmissionsTable.Meta):
        fields = ('title', 'status_name', 'stage', 'page', 'round', 'lead', 'submit_time')  # type: ignore
        sequence = fields + ('comments',)


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


def get_round_leads(request):
    User = get_user_model()
    return User.objects.filter(round__isnull=False).distinct()


class Select2CheckboxWidgetMixin(filters.Filter):
    def __init__(self, *args, **kwargs):
        label = kwargs.get('label')
        kwargs.setdefault('widget', Select2MultiCheckboxesWidget(attrs={'data-placeholder': label}))
        super().__init__(*args, **kwargs)


class Select2MultipleChoiceFilter(Select2CheckboxWidgetMixin, filters.MultipleChoiceFilter):
    pass


class Select2ModelMultipleChoiceFilter(Select2MultipleChoiceFilter, filters.ModelMultipleChoiceFilter):
    pass


class SubmissionFilter(filters.FilterSet):
    round = Select2ModelMultipleChoiceFilter(queryset=get_used_rounds, label='Rounds')
    funds = Select2ModelMultipleChoiceFilter(name='page', queryset=get_used_funds, label='Funds')
    status = Select2MultipleChoiceFilter(name='status__contains', choices=status_options, label='Statuses')
    lead = Select2ModelMultipleChoiceFilter(queryset=get_round_leads, label='Leads')

    class Meta:
        model = ApplicationSubmission
        fields = ('funds', 'round', 'status')


class SubmissionFilterAndSearch(SubmissionFilter):
    query = filters.CharFilter(name='search_data', lookup_expr="search", widget=forms.HiddenInput)
