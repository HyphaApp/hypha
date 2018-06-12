from django import forms
from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery, F, Q
from django.utils.text import mark_safe, slugify

import django_filters as filters
import django_tables2 as tables
from django_tables2.utils import A

from wagtail.core.models import Page

from opentech.apply.activity.models import Activity
from opentech.apply.funds.models import ApplicationSubmission, Round
from opentech.apply.funds.workflow import STATUSES
from opentech.apply.users.groups import STAFF_GROUP_NAME
from .widgets import Select2MultiCheckboxesWidget


def make_row_class(record):
    css_class = 'all-submissions__child' if record.next else 'all-submissions__parent'
    css_class += '' if record.active else ' is-inactive'
    return css_class


class SubmissionsTable(tables.Table):
    """Base table for listing submissions, do not include admin data to this table"""
    title = tables.LinkColumn('funds:submissions:detail', args=[A('pk')], orderable=True)
    submit_time = tables.DateColumn(verbose_name="Submitted")
    phase = tables.Column(verbose_name="Status", order_by=('status',))
    stage = tables.Column(verbose_name="Type", order_by=('status',))
    page = tables.Column(verbose_name="Fund")
    comments = tables.Column(accessor='activities.comments.all', verbose_name="Comments")
    last_update = tables.DateColumn(accessor="activities.first.timestamp", verbose_name="Last updated")

    class Meta:
        model = ApplicationSubmission
        order_by = ('-last_update',)
        fields = ('title', 'phase', 'stage', 'page', 'round', 'submit_time', 'last_update')
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
        return mark_safe(f'<span>{ value }</span>')

    def render_comments(self, value):
        request = self.context['request']
        return str(value.visible_to(request.user).count())

    def order_last_update(self, qs, desc):
        update_order = getattr(F('last_update'), 'desc' if desc else 'asc')(nulls_last=True)

        related_actions = Activity.objects.filter(submission=OuterRef('id'))
        qs = qs.annotate(
            last_update=Subquery(related_actions.values('timestamp')[:1])
        ).order_by(update_order, 'submit_time')

        return qs, True


class AdminSubmissionsTable(SubmissionsTable):
    """Adds admin only columns to the submissions table"""
    lead = tables.Column(order_by=('lead.full_name',))
    reviews_stats = tables.TemplateColumn(template_name='funds/tables/column_reviews.html', verbose_name=mark_safe("Reviews\n<span>Assgn.\tComp.</span>"), orderable=False)

    class Meta(SubmissionsTable.Meta):
        fields = ('title', 'phase', 'stage', 'page', 'round', 'lead', 'submit_time', 'last_update', 'reviews_stats')  # type: ignore
        sequence = fields + ('comments',)


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


def get_round_leads(request):
    User = get_user_model()
    return User.objects.filter(round_lead__isnull=False).distinct()


def get_reviewers(request):
    """ All assigned reviewers, staff or admin """
    User = get_user_model()
    return User.objects.filter(Q(submissions_reviewer__isnull=False) | Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)).distinct()


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
    funds = Select2ModelMultipleChoiceFilter(name='page', queryset=get_used_funds, label='Funds')
    status = StatusMultipleChoiceFilter()
    lead = Select2ModelMultipleChoiceFilter(queryset=get_round_leads, label='Leads')
    reviewers = Select2ModelMultipleChoiceFilter(queryset=get_reviewers, label='Reviewers')

    class Meta:
        model = ApplicationSubmission
        fields = ('funds', 'round', 'status')


class SubmissionFilterAndSearch(SubmissionFilter):
    query = filters.CharFilter(name='search_data', lookup_expr="search", widget=forms.HiddenInput)
