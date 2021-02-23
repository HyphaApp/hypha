from django.db.models import Q
from django_filters import rest_framework as filters
from wagtail.core.models import Page

from hypha.apply.activity.models import Activity
from hypha.apply.funds.models import (
    ApplicationSubmission,
    FundType,
    LabType,
    RoundsAndLabs,
)
from hypha.apply.funds.workflow import PHASES

from .utils import get_reviewers, get_round_leads, get_screening_statuses


class RoundLabFilter(filters.ModelChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs

        return qs.filter(Q(round=value) | Q(page=value))


class SubmissionsFilter(filters.FilterSet):
    round = RoundLabFilter(queryset=RoundsAndLabs.objects.all())
    status = filters.MultipleChoiceFilter(choices=PHASES)
    active = filters.BooleanFilter(method='filter_active', label='Active')
    submit_date = filters.DateFromToRangeFilter(field_name='submit_time', label='Submit date')
    fund = filters.ModelMultipleChoiceFilter(
        field_name='page', label='fund',
        queryset=Page.objects.type(FundType) | Page.objects.type(LabType)
    )
    screening_statuses = filters.ModelMultipleChoiceFilter(
        field_name='screening_statuses',
        queryset=get_screening_statuses(),
    )
    reviewers = filters.ModelMultipleChoiceFilter(
        field_name='reviewers',
        queryset=get_reviewers(),
    )
    lead = filters.ModelMultipleChoiceFilter(
        field_name='lead',
        queryset=get_round_leads(),
    )
    id = filters.ModelMultipleChoiceFilter(
        field_name='id',
        queryset=ApplicationSubmission.objects.current().with_latest_update(),
        method='filter_id'
    )

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'status', 'round', 'active', 'submit_date', 'fund', 'screening_statuses', 'reviewers', 'lead')

    def filter_active(self, qs, name, value):
        if value is None:
            return qs

        if value:
            return qs.active()
        else:
            return qs.inactive()

    def filter_id(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(id__in=self.request.GET.getlist('id'))


class NewerThanFilter(filters.ModelChoiceFilter):
    def filter(self, qs, value):
        if not value:
            return qs

        return qs.newer(value)


class CommentFilter(filters.FilterSet):
    since = filters.DateTimeFilter(field_name="timestamp", lookup_expr='gte')
    before = filters.DateTimeFilter(field_name="timestamp", lookup_expr='lte')
    newer = NewerThanFilter(queryset=Activity.comments.all())

    class Meta:
        model = Activity
        fields = ['visibility', 'since', 'before', 'newer']


class AllCommentFilter(CommentFilter):
    class Meta(CommentFilter.Meta):
        fields = CommentFilter.Meta.fields + ['source_object_id']
