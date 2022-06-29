from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from wagtail.core.models import Page

from hypha.apply.activity.models import Activity
from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.categories.models import Option
from hypha.apply.funds.models import ApplicationSubmission, FundType, LabType
from hypha.apply.funds.workflow import PHASES

from .utils import (
    get_reviewers,
    get_round_leads,
    get_screening_statuses,
    get_used_rounds,
)


class SubmissionsFilter(filters.FilterSet):
    round = filters.ModelMultipleChoiceFilter(field_name='round', queryset=get_used_rounds())
    status = filters.MultipleChoiceFilter(choices=PHASES)
    active = filters.BooleanFilter(method='filter_active', label=_('Active'))
    submit_date = filters.DateFromToRangeFilter(field_name='submit_time', label=_('Submit date'))
    fund = filters.ModelMultipleChoiceFilter(
        field_name='page', label=_('fund'),
        queryset=Page.objects.type(FundType) | Page.objects.type(LabType)
    )
    screening_statuses = filters.ModelMultipleChoiceFilter(
        field_name='screening_statuses',
        queryset=get_screening_statuses(),
        null_label=_('No Screening')
    )
    reviewers = filters.ModelMultipleChoiceFilter(
        field_name='reviewers',
        queryset=get_reviewers(),
    )
    lead = filters.ModelMultipleChoiceFilter(
        field_name='lead',
        queryset=get_round_leads(),
    )
    category_options = filters.MultipleChoiceFilter(
        choices=[], label=_('Category'),
        method='filter_category_options'
    )
    id = filters.ModelMultipleChoiceFilter(
        field_name='id',
        queryset=ApplicationSubmission.objects.exclude_draft().current().with_latest_update(),
        method='filter_id'
    )

    class Meta:
        model = ApplicationSubmission
        fields = ('id', 'status', 'round', 'active', 'submit_date', 'fund', 'screening_statuses', 'reviewers', 'lead')

    def __init__(self, *args, exclude=list(), limit_statuses=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['category_options'].extra['choices'] = [
            (option.id, option.value)
            for option in Option.objects.filter(category__filter_on_dashboard=True)
        ]

    def filter_active(self, qs, name, value):
        if value is None:
            return qs

        if value:
            return qs.active()
        else:
            return qs.inactive()

    def filter_category_options(self, queryset, name, value):
        """
        Filter submissions based on the category options selected.

        In order to do that we need to first get all the category fields used in the submission.

        And then use those category fields to filter submissions with their form_data.
        """
        query = Q()
        submission_data = queryset.values('form_fields', 'form_data').distinct()
        for submission in submission_data:
            for field in submission['form_fields']:
                if isinstance(field.block, CategoryQuestionBlock):
                    try:
                        category_options = category_ids = submission['form_data'][field.id]
                    except KeyError:
                        include_in_filter = False
                    else:
                        if isinstance(category_options, str):
                            category_options = [category_options]
                        include_in_filter = set(list(category_options)) & set(value)
                    # Check if filter options has any value in category options
                    # If yes then those submissions should be filtered in the list
                    if include_in_filter:
                        kwargs = {
                            '{0}__{1}'.format('form_data', field.id): category_ids
                        }
                        query |= Q(**kwargs)
        return queryset.filter(query)

    def filter_id(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(id__in=map(lambda x: x.id, value))


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
