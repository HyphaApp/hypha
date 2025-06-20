import json
import re

import django_filters as filters
import django_tables2 as tables
from django import forms
from django.contrib.auth import get_user_model
from django.db.models import F, Q
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_tables2.utils import A
from wagtail.models import Page

from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.categories.models import MetaTerm, Option
from hypha.apply.funds.reviewers.services import get_all_reviewers
from hypha.apply.review.models import Review

from .models import ApplicationSubmission, Round, ScreeningStatus
from .widgets import MultiCheckboxesWidget
from .workflows import STATUSES

User = get_user_model()


def render_actions(table, record):
    user = table.context["user"]
    actions = record.get_actions_for_user(user)
    return json.dumps([slugify(action) for _, action in actions])


def render_title(record):
    try:
        title = record.title_text_display
    except AttributeError:
        title = record.submission.title_text_display
    return title


def render_reviewer_link(record):
    return f"{reverse('funds:submissions:list')}?reviewers={record.id}"


class SubmissionsTable(tables.Table):
    """Base table for listing submissions, do not include admin data to this table"""

    title = tables.LinkColumn(
        "funds:submissions:detail",
        text=render_title,
        args=[A("pk")],
        orderable=True,
        attrs={
            "td": {
                "class": "js-title max-w-sm",
            },
            "a": {
                "data-tippy-content": lambda record: render_title(record),
                "data-tippy-placement": "top",
                # Use after:content-[''] after:block to hide the default browser tooltip on Safari
                # https://stackoverflow.com/a/43915246
                "class": "link link-hover text-h4 font-semibold truncate inline-block w-[calc(100%-2rem)] after:content-[''] after:block",
            },
        },
    )
    submit_time = tables.DateColumn(verbose_name=_("Submitted"))
    phase = tables.Column(
        verbose_name=_("Status"),
        order_by=("status",),
        attrs={"td": {"data-actions": render_actions, "class": "js-actions"}},
    )
    stage = tables.Column(verbose_name=_("Type"), order_by=("status",))
    fund = tables.Column(verbose_name=_("Fund"), accessor="page")
    comments = tables.Column(accessor="comment_count", verbose_name=_("Comments"))
    last_update = tables.DateColumn(
        accessor="last_update", verbose_name=_("Last updated")
    )

    class Meta:
        model = ApplicationSubmission
        order_by = ("-last_update",)
        fields = (
            "title",
            "phase",
            "stage",
            "fund",
            "round",
            "submit_time",
            "last_update",
        )
        sequence = fields + ("comments",)
        template_name = "funds/tables/table.html"
        row_attrs = {
            "data-record-id": lambda record: record.id,
            "data-archived": lambda record: record.is_archive,
        }
        attrs = {"class": "table all-submissions-table"}
        empty_text = _("No submissions available")

    def render_user(self, value):
        return value.get_full_name()

    def render_phase(self, value):
        return format_html("<span>{}</span>", value)

    def order_last_update(self, qs, desc):
        update_order = getattr(F("last_update"), "desc" if desc else "asc")(
            nulls_last=True
        )

        qs = qs.order_by(update_order, "submit_time")
        return qs, True

    def get_column_class_names(self, classes_set, bound_column):
        classes_set = super(SubmissionsTable, self).get_column_class_names(
            classes_set, bound_column
        )
        classes_set.add(bound_column.name)
        return classes_set


class ReviewerSubmissionsTable(SubmissionsTable):
    class Meta(SubmissionsTable.Meta):
        orderable = False


class LabeledCheckboxColumn(tables.CheckBoxColumn):
    def wrap_with_label(self, checkbox, for_value):
        return format_html(
            '<label for="{}">{}</label>',
            for_value,
            checkbox,
        )

    @property
    def header(self):
        checkbox = super().header
        return self.wrap_with_label(checkbox, "selectall")

    def render(self, value, record, bound_column):
        checkbox = super().render(value=value, record=record, bound_column=bound_column)
        return self.wrap_with_label(checkbox, value)


class BaseAdminSubmissionsTable(SubmissionsTable):
    lead = tables.Column(order_by=("lead__full_name",))
    reviews_stats = tables.TemplateColumn(
        template_name="funds/tables/column_reviews.html",
        verbose_name=mark_safe(
            'Reviews<div>Comp. <span class="counts-separator">/</span> Assgn.</div>'
        ),
        orderable=False,
    )
    screening_status = tables.Column(
        verbose_name=_("Screening"), accessor="screening_statuses"
    )
    organization_name = tables.Column()

    class Meta(SubmissionsTable.Meta):
        fields = (
            "title",
            "phase",
            "stage",
            "fund",
            "round",
            "lead",
            "submit_time",
            "last_update",
            "screening_status",
            "reviews_stats",
            "organization_name",
        )
        sequence = fields + ("comments",)

    def render_lead(self, value):
        return format_html("<span>{}</span>", value)

    def render_screening_status(self, value):
        try:
            status = value.get()
            classname = "status-yes" if status.yes else "status-no text-red-500"
            return format_html(
                f"<span class='font-medium text-xs {classname}'>{'👍' if status.yes else '👎'} {status.title}</span>"
            )
        except ScreeningStatus.DoesNotExist:
            return format_html(
                "<span class='text-xs text-fg-muted'>{}</span>", "Awaiting"
            )


def get_used_rounds(request):
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds(request):
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


def get_round_leads(request):
    return User.objects.filter(submission_lead__isnull=False).distinct()


def get_screening_statuses(request):
    return ScreeningStatus.objects.filter(
        id__in=ApplicationSubmission.objects.all()
        .values("screening_statuses__id")
        .distinct("screening_statuses__id")
    )


def get_meta_terms(request):
    return MetaTerm.objects.filter(
        filter_on_dashboard=True,
        id__in=ApplicationSubmission.objects.all()
        .values("meta_terms__id")
        .distinct("meta_terms__id"),
    )


class MultiCheckboxesMixin(filters.Filter):
    def __init__(self, *args, **kwargs):
        label = kwargs.get("label")
        kwargs.setdefault(
            "widget", MultiCheckboxesWidget(attrs={"data-placeholder": label})
        )
        super().__init__(*args, **kwargs)


class MultipleChoiceFilter(MultiCheckboxesMixin, filters.MultipleChoiceFilter):
    pass


class ModelMultipleChoiceFilter(
    MultipleChoiceFilter, filters.ModelMultipleChoiceFilter
):
    pass


class StatusMultipleChoiceFilter(MultipleChoiceFilter):
    def __init__(self, limit_to, *args, **kwargs):
        choices = [
            (slugify(name), name)
            for name, statuses in STATUSES.items()
            if not limit_to or self.has_any(statuses, limit_to)
        ]
        self.status_map = {
            slugify(name): list(status) for name, status in STATUSES.items()
        }
        super().__init__(
            *args,
            field_name="status",
            choices=choices,
            label=_("Statuses"),
            **kwargs,
        )

    def has_any(self, first, second):
        return any(item in second for item in first)

    def get_filter_predicate(self, v):
        return {f"{self.field_name}__in": self.status_map.get(v, [])}


class SubmissionFilter(filters.FilterSet):
    fund = ModelMultipleChoiceFilter(
        field_name="page", queryset=get_used_funds, label=_("Funds")
    )
    round = ModelMultipleChoiceFilter(queryset=get_used_rounds, label=_("Rounds"))
    lead = ModelMultipleChoiceFilter(queryset=get_round_leads, label=_("Leads"))
    screening_statuses = ModelMultipleChoiceFilter(
        queryset=get_screening_statuses, label=_("Screening"), null_label=_("No Status")
    )
    reviewers = ModelMultipleChoiceFilter(
        queryset=get_all_reviewers, label=_("Reviewers")
    )
    category_options = MultipleChoiceFilter(
        choices=[], label=_("Category"), method="filter_category_options"
    )
    meta_terms = ModelMultipleChoiceFilter(queryset=get_meta_terms, label=_("Tags"))

    class Meta:
        model = ApplicationSubmission
        fields = ("fund", "round")

    def __init__(self, *args, exclude=None, limit_statuses=None, **kwargs):
        if exclude is None:
            exclude = []

        super().__init__(*args, **kwargs)

        self.filters["status"] = StatusMultipleChoiceFilter(limit_to=limit_statuses)
        self.filters["category_options"].extra["choices"] = [
            (option.id, option.value)
            for option in Option.objects.filter(category__filter_on_dashboard=True)
        ]
        self.filters = {
            field: filter
            for field, filter in self.filters.items()
            if field not in exclude
        }

    def filter_category_options(self, queryset, name, value):
        """
        Filter submissions based on the category options selected.

        In order to do that we need to first get all the category fields used in the submission.

        And then use those category fields to filter submissions with their form_data.
        """
        query = Q()
        submission_data = queryset.values("form_fields", "form_data").distinct()
        for submission in submission_data:
            for field in submission["form_fields"]:
                if isinstance(field.block, CategoryQuestionBlock):
                    try:
                        category_options = category_ids = submission["form_data"][
                            field.id
                        ]
                    except KeyError:
                        include_in_filter = False
                    else:
                        if isinstance(category_options, str):
                            category_options = [category_options]
                        include_in_filter = set(category_options) & set(value)
                    # Check if filter options has any value in category options
                    # If yes then those submissions should be filtered in the list
                    if include_in_filter:
                        kwargs = {
                            "{0}__{1}".format("form_data", field.id): category_ids
                        }
                        query |= Q(**kwargs)
        return queryset.filter(query)


class SubmissionFilterAndSearch(SubmissionFilter):
    query = filters.CharFilter(method="search_data_and_id", widget=forms.HiddenInput)
    archived = filters.BooleanFilter(
        field_name="is_archive", widget=forms.HiddenInput, method="filter_archived"
    )

    def search_data_and_id(self, queryset, name, value):
        possible_id = re.search("^#(\\d+)$", value.strip())
        if possible_id:
            return queryset.filter(id=possible_id.groups()[0])
        return queryset.filter(search_data__icontains=value)

    def filter_archived(self, queryset, name, value):
        if not value:
            # if value is 0 or None
            queryset = queryset.exclude(is_archive=True)
        return queryset


class SubmissionDashboardFilter(filters.FilterSet):
    round = ModelMultipleChoiceFilter(queryset=get_used_rounds, label=_("Rounds"))
    fund = ModelMultipleChoiceFilter(
        field_name="page", queryset=get_used_funds, label=_("Funds")
    )

    class Meta:
        model = ApplicationSubmission
        fields = ("fund", "round")

    def __init__(self, *args, exclude=None, limit_statuses=None, **kwargs):
        if exclude is None:
            exclude = []
        super().__init__(*args, **kwargs)

        self.filters = {
            field: filter
            for field, filter in self.filters.items()
            if field not in exclude
        }


class RoundsTable(tables.Table):
    title = tables.Column(
        linkify=lambda record: record.get_absolute_url(),
        orderable=True,
    )
    fund = tables.Column(accessor=A("specific__fund"))
    lead = tables.Column()
    start_date = tables.Column()
    end_date = tables.Column()
    deterrmined = tables.Column(verbose_name=_("Determined"), accessor="progress")

    def __init__(self, *args, **kwargs):
        self.prefix = kwargs.pop("prefix", "rounds")
        super().__init__(*args, **kwargs)

    class Meta:
        fields = ("title", "fund", "lead", "start_date", "end_date", "deterrmined")
        attrs = {"class": "table"}

    def render_lead(self, value):
        return format_html("<span>{}</span>", value)

    def render_deterrmined(self, record):
        return f"{record.progress}%"

    def _field_order(self, field, desc):
        return getattr(F(f"{field}"), "desc" if desc else "asc")(nulls_last=True)

    def order_start_date(self, qs, desc):
        return qs.order_by(self._field_order("start_date", desc)), True

    def order_end_date(self, qs, desc):
        return qs.order_by(self._field_order("end_date", desc)), True

    def order_fund(self, qs, desc):
        return qs.order_by(self._field_order("fund", desc)), True

    def order_progress(self, qs, desc):
        return qs.order_by(self._field_order("progress", desc)), True

    def get_column_class_names(self, classes_set, bound_column):
        classes_set = super(RoundsTable, self).get_column_class_names(
            classes_set, bound_column
        )
        classes_set.add(bound_column.name)
        return classes_set


class ActiveRoundFilter(MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            self,
            *args,
            choices=[("active", "Active"), ("inactive", "Inactive")],
            **kwargs,
        )

    def filter(self, qs, value):
        if value is None or len(value) != 1:
            return qs

        value = value[0]
        if value == "active":
            return qs.active()
        else:
            return qs.inactive()


class OpenRoundFilter(MultipleChoiceFilter):
    def __init__(self, *args, **kwargs):
        super().__init__(
            self,
            *args,
            choices=[("open", "Open"), ("closed", "Closed"), ("new", "Not Started")],
            **kwargs,
        )

    def filter(self, qs, value):
        if value is None or len(value) != 1:
            return qs

        value = value[0]
        if value == "closed":
            return qs.closed()
        if value == "new":
            return qs.new()

        return qs.open()


class RoundsFilter(filters.FilterSet):
    fund = ModelMultipleChoiceFilter(queryset=get_used_funds, label=_("Funds"))
    lead = ModelMultipleChoiceFilter(queryset=get_round_leads, label=_("Leads"))
    active = ActiveRoundFilter(label=_("Active"))
    round_state = OpenRoundFilter(label=_("Open"))


class ReviewerLeaderboardFilterForm(forms.ModelForm):
    """
    Form to "clean" a list of User objects to their PKs.

    The Reviewer Leaderboard table is a list of User objects, however we also want
    the ability to filter down to N Users (reviewers).  Django filter is converting
    the selected PKs to User objects, however we can't filter a User QuerySet
    with User objects.  So this form converts back to a list of User PKs using
    the clean_reviewer method.
    """

    class Meta:
        fields = ["id"]
        model = User

    def clean_reviewer(self):
        return [u.id for u in self.cleaned_data["reviewer"]]


class ReviewerLeaderboardFilter(filters.FilterSet):
    query = filters.CharFilter(
        field_name="full_name", lookup_expr="icontains", widget=forms.HiddenInput
    )

    reviewer = ModelMultipleChoiceFilter(
        field_name="pk",
        label=_("Reviewers"),
        queryset=get_all_reviewers,
    )
    funds = ModelMultipleChoiceFilter(
        field_name="applicationsubmission__page",
        label=_("Funds"),
        queryset=get_used_funds,
    )
    rounds = ModelMultipleChoiceFilter(
        field_name="applicationsubmission__round",
        label=_("Rounds"),
        queryset=get_used_rounds,
    )

    class Meta:
        fields = [
            "reviewer",
            "funds",
            "rounds",
        ]
        form = ReviewerLeaderboardFilterForm
        model = User


class ReviewerLeaderboardTable(tables.Table):
    full_name = tables.LinkColumn(
        "funds:submissions:reviewer_leaderboard_detail",
        args=[A("pk")],
        orderable=True,
        verbose_name=_("Reviewer"),
        attrs={
            "a": {"class": "link link-hover text-h4 font-semibold"},
            "td": {"class": "title"},
        },
    )

    class Meta:
        model = User
        fields = [
            "full_name",
            "ninety_days",
            "this_year",
            "last_year",
            "total",
        ]
        order_by = ("-ninety_days",)
        attrs = {"class": "table"}
        empty_text = _("No reviews available")


class ReviewerLeaderboardDetailTable(tables.Table):
    title = tables.LinkColumn(
        "funds:submissions:reviews:review",
        text=render_title,
        args=[A("submission_id"), A("pk")],
        orderable=True,
        verbose_name=_("Submission"),
        attrs={
            "td": {
                "class": "js-title",
            },
            "a": {
                "data-tippy-content": lambda record: render_title(record),
                "data-tippy-placement": "top",
                # Use after:content-[''] after:block to hide the default browser tooltip on Safari
                # https://stackoverflow.com/a/43915246
                "class": "link link-hover text-h4 font-semibold truncate inline-block w-[calc(100%-2rem)] after:content-["
                "] after:block",
            },
        },
    )

    class Meta:
        model = Review
        fields = [
            "title",
            "recommendation",
            "created_at",
        ]
        order_by = ("-created_at",)
        attrs = {"class": "table"}
        empty_text = _("No reviews available")


class StaffAssignmentsTable(tables.Table):
    full_name = tables.Column(
        linkify=render_reviewer_link,
        orderable=True,
        verbose_name=_("Staff"),
        attrs={"td": {"class": "title"}},
    )

    class Meta:
        model = User
        fields = [
            "full_name",
        ]
        attrs = {"class": "table"}
        empty_text = _("No staff available")
