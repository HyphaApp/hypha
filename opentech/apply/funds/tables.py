import textwrap

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.utils.html import format_html
from django.utils.text import mark_safe, slugify

import django_filters as filters
import django_tables2 as tables
from django_tables2.utils import A

from wagtail.core.models import Page

from opentech.apply.funds.models import ApplicationSubmission, Round, ScreeningStatus
from opentech.apply.funds.workflow import STATUSES
from opentech.apply.users.groups import STAFF_GROUP_NAME
from .widgets import Select2MultiCheckboxesWidget


def make_row_class(record):
    css_class = 'submission-meta__row' if record.next else 'all-submissions__parent'
    css_class += '' if record.active else ' is-inactive'
    return css_class


def render_title(record):
    return textwrap.shorten(record.title, width=30, placeholder="...")


class SubmissionsTable(tables.Table):
    """Base table for listing submissions, do not include admin data to this table"""
    title = tables.LinkColumn('funds:submissions:detail', text=render_title, args=[A('pk')], orderable=True, attrs={'td': {'data-tooltip': lambda record: record.title, 'class': 'js-title'}})
    submit_time = tables.DateColumn(verbose_name="Submitted")
    phase = tables.Column(verbose_name="Status", order_by=('status',))
    stage = tables.Column(verbose_name="Type", order_by=('status',))
    fund = tables.Column(verbose_name="Fund", accessor='page')
    comments = tables.Column(accessor='comment_count', verbose_name="Comments")
    last_update = tables.DateColumn(accessor="last_update", verbose_name="Last updated")

    class Meta:
        model = ApplicationSubmission
        order_by = ('-last_update',)
        fields = ('title', 'phase', 'stage', 'fund', 'round', 'submit_time', 'last_update')
        sequence = fields + ('comments',)
        template_name = 'funds/tables/table.html'
        row_attrs = {
            'class': make_row_class,
            'data-record-id': lambda record: record.id,
        }
        attrs = {'class': 'all-submissions'}

    def render_user(self, value):
        return value.get_full_name()

    def render_phase(self, value):
        return format_html('<span>{}</span>', value)

    def order_last_update(self, qs, desc):
        update_order = getattr(F('last_update'), 'desc' if desc else 'asc')(nulls_last=True)

        qs = qs.order_by(update_order, 'submit_time')
        return qs, True


class AdminSubmissionsTable(SubmissionsTable):
    """Adds admin only columns to the submissions table"""
    lead = tables.Column(order_by=('lead.full_name',))
    reviews_stats = tables.TemplateColumn(template_name='funds/tables/column_reviews.html', verbose_name=mark_safe("Reviews\n<span>Assgn.\tComp.</span>"), orderable=False)
    screening_status = tables.Column(verbose_name="Screening")

    class Meta(SubmissionsTable.Meta):
        fields = ('title', 'phase', 'stage', 'fund', 'round', 'lead', 'submit_time', 'last_update', 'screening_status', 'reviews_stats')  # type: ignore
        sequence = fields + ('comments',)

    def render_lead(self, value):
        return format_html('<span>{}</span>', value)


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


def get_round_leads(request):
    User = get_user_model()
    return User.objects.filter(roundbase_lead__isnull=False).distinct()


def get_reviewers(request):
    """ All assigned reviewers, staff or admin """
    User = get_user_model()
    return User.objects.filter(Q(submissions_reviewer__isnull=False) | Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)).distinct()


def get_screening_statuses(request):
    return ScreeningStatus.objects.filter(
        id__in=ApplicationSubmission.objects.all().values('screening_status__id').distinct('screening_status__id'))


class Select2CheckboxWidgetMixin(filters.Filter):
    def __init__(self, *args, **kwargs):
        label = kwargs.get('label')
        kwargs.setdefault('widget', Select2MultiCheckboxesWidget(attrs={'data-placeholder': label}))
        super().__init__(*args, **kwargs)


class Select2MultipleChoiceFilter(Select2CheckboxWidgetMixin, filters.MultipleChoiceFilter):
    pass


class Select2ModelMultipleChoiceFilter(Select2MultipleChoiceFilter, filters.ModelMultipleChoiceFilter):
    pass


class StatusMultipleChoiceFilter(Select2MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        choices = [(slugify(status), status) for status in STATUSES]
        self.status_map = {slugify(name): status for name, status in STATUSES.items()}
        super().__init__(
            *args,
            name='status',
            choices=choices,
            label='Statuses',
            **kwargs,
        )

    def get_filter_predicate(self, v):
        return {f'{ self.field_name }__in': self.status_map[v]}


class SubmissionFilter(filters.FilterSet):
    round = Select2ModelMultipleChoiceFilter(queryset=get_used_rounds, label='Rounds')
    fund = Select2ModelMultipleChoiceFilter(name='page', queryset=get_used_funds, label='Funds')
    status = StatusMultipleChoiceFilter()
    lead = Select2ModelMultipleChoiceFilter(queryset=get_round_leads, label='Leads')
    reviewers = Select2ModelMultipleChoiceFilter(queryset=get_reviewers, label='Reviewers')
    screening_status = Select2ModelMultipleChoiceFilter(queryset=get_screening_statuses, label='Screening')

    class Meta:
        model = ApplicationSubmission
        fields = ('fund', 'round', 'status')

    def __init__(self, *args, exclude=list(), **kwargs):
        super().__init__(*args, **kwargs)

        self.filters = {
            field: filter
            for field, filter in self.filters.items()
            if field not in exclude
        }


class SubmissionFilterAndSearch(SubmissionFilter):
    query = filters.CharFilter(field_name='search_data', lookup_expr="icontains", widget=forms.HiddenInput)


class RoundsTable(tables.Table):
    title = tables.LinkColumn('funds:rounds:detail', args=[A('pk')], orderable=True, text=lambda record: record.title)
    fund = tables.Column(accessor=A('specific.fund'))
    lead = tables.Column()
    start_date = tables.Column()
    end_date = tables.Column()
    progress = tables.Column(verbose_name="Determined")

    class Meta:
        fields = ('title', 'fund', 'lead', 'start_date', 'end_date', 'progress')

    def render_lead(self, value):
        return format_html('<span>{}</span>', value)

    def render_progress(self, record):
        return f'{record.progress}%'

    def _field_order(self, field, desc):
        return getattr(F(f'{field}'), 'desc' if desc else 'asc')(nulls_last=True)

    def order_start_date(self, qs, desc):
        return qs.order_by(self._field_order('start_date', desc)), True

    def order_end_date(self, qs, desc):
        return qs.order_by(self._field_order('end_date', desc)), True

    def order_fund(self, qs, desc):
        return qs.order_by(self._field_order('fund', desc)), True

    def order_progress(self, qs, desc):
        return qs.order_by(self._field_order('progress', desc)), True


class ActiveRoundFilter(Select2MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, choices=[('active', 'Active'), ('inactive', 'Inactive')], **kwargs)

    def filter(self, qs, value):
        if value is None or len(value) != 1:
            return qs

        value = value[0]
        if value == 'active':
            return qs.active()
        else:
            return qs.inactive()


class OpenRoundFilter(Select2MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, choices=[('open', 'Open'), ('closed', 'Closed'), ('new', 'Not Started')], **kwargs)

    def filter(self, qs, value):
        if value is None or len(value) != 1:
            return qs

        value = value[0]
        if value == 'closed':
            return qs.closed()
        if value == 'new':
            return qs.new()

        return qs.open()


class RoundsFilter(filters.FilterSet):
    fund = Select2ModelMultipleChoiceFilter(queryset=get_used_funds, label='Funds')
    lead = Select2ModelMultipleChoiceFilter(queryset=get_round_leads, label='Leads')
    active = ActiveRoundFilter(label='Active')
    round_state = OpenRoundFilter(label='Open')
