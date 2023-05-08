import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.text import slugify
from django.utils.translation import gettext as _
from wagtail.models import Page

from hypha.apply.funds.workflow import PHASES
from hypha.apply.search.filters import apply_date_filter
from hypha.apply.search.query_parser import parse_search_query

from .models import (
    ApplicationSubmission,
    Round,
)
from .permissions import is_user_has_access_to_view_archived_submissions
from .tables import (
    SubmissionFilter,
)

User = get_user_model()


@login_required
def submission_all_beta(request: HttpRequest, template_name='submissions/all.html') -> HttpResponse:
    search_query = request.GET.get('query') or ""
    parsed_query = parse_search_query(search_query)
    search_term, search_filters = parsed_query['text'], parsed_query['filters']

    show_archived = request.GET.get("archived", False) == 'on'
    selected_funds = request.GET.getlist("fund")
    selected_rounds = request.GET.getlist("round")
    selected_leads = request.GET.getlist("lead")
    selected_statuses = request.GET.getlist("status")
    selected_reviewers = request.GET.getlist("reviewers")
    selected_meta_terms = request.GET.getlist("meta_terms")
    selected_category_options = request.GET.getlist("category_options")
    selected_sort = request.GET.get("sort")
    page = request.GET.get("page", 1)

    selected_fund_objects = Page.objects.filter(id__in=selected_funds) if selected_funds else []
    selected_round_objects = Round.objects.filter(id__in=selected_rounds) if selected_rounds else []

    if request.htmx:
        base_template = "includes/_partial-main.html"
    else:
        base_template = "funds/base_submissions_table.html"

    start = time.time()

    if show_archived:
        qs = ApplicationSubmission.objects.include_archive().for_table(request.user)
    else:
        qs = ApplicationSubmission.objects.current().for_table(request.user)

    qs = qs.prefetch_related('meta_terms')

    match search_filters:
        case {'submitted': values}:
            qs = apply_date_filter(qs=qs, field='submit_time', values=values)
        case {'updated': values}:
            qs = apply_date_filter(qs=qs, field='last_update', values=values)
        case {'is': values}:
            if 'archived' in values:
                qs = qs.filter(is_archive=True)

    if search_term:
        query = SearchQuery(search_term, search_type='websearch')
        rank_annotation = SearchRank(models.F('search_document'), query)
        qs = qs.filter(search_document=query)
        qs = qs.annotate(rank=rank_annotation)

    filter_extras = {
        'exclude': settings.SUBMISSIONS_TABLE_EXCLUDED_FIELDS,
    }

    if selected_funds:
        qs = qs.filter(page__in=selected_funds)

    # if selected_statuses:
    #     qs = qs.filter(status__in=selected_statuses)

    status_count_raw = {}
    # year_counts_raw = {}
    # month_counts_raw = {}

    # Status Filter Options
    STATUS_MAP = {k: phase.display_name for k, phase in PHASES}
    for row in qs.order_by().values('status').annotate(
        n=models.Count('status')
    ):
        status_display = STATUS_MAP[row['status']]
        try:
            count = status_count_raw[status_display]['count']
        except KeyError:
            count = 0
        status_count_raw[status_display] = {
            'count': count + row['n'],
            'title': status_display,
            'slug': slugify(status_display).lower(),
            'selected': status_display in selected_statuses,
        }

    status_counts = sorted(
        status_count_raw.values(),
        key=lambda t: (t['selected'], t['count']), reverse=True
    )

    filter_kwargs = {**request.GET, **filter_extras}
    filters = SubmissionFilter(filter_kwargs, queryset=qs)
    is_filtered = any([
        selected_fund_objects,
        selected_statuses,
        selected_round_objects,
        selected_leads,
        selected_reviewers,
        selected_meta_terms,
        selected_category_options,
        selected_sort,
    ])

    qs = filters.qs

    sort_options_raw = {
        "submitted-desc": ("-submit_time", _('Newest')),
        "submitted-asc": ("submit_time", _('Oldest')),
        "comments-desc": ("-comment_count", _('Most Commented')),
        "comments-asc": ("comment_count", _('Least Commented')),
        "updated-desc": ("-last_update", _('Recently Updated')),
        "updated-asc": ("last_update", _('Least Recently Updated')),
        "relevance-desc": ("-rank", _('Best Match')),
    }

    sort_options = [{
        'name': v[1],
        'param': k,
        'selected': selected_sort == k
    } for k, v in sort_options_raw.items()]

    if selected_sort and selected_sort in sort_options_raw.keys():
        if not search_query and selected_sort == 'relevance-desc':
            qs = qs.order_by('-submit_time')
        else:
            qs = qs.order_by(sort_options_raw[selected_sort][0])
    elif search_term:
        qs = qs.order_by('-rank')
    else:
        qs = qs.order_by("-submit_time")

    end = time.time()

    page = Paginator(qs, per_page=60, orphans=20).page(page)

    ctx = {
        'base_template': base_template,
        'search_query': search_query,
        'filters': filters,
        'page': page,
        'submissions': page.object_list,
        'submission_ids': [x.id for x in page.object_list],
        'show_archived': show_archived,
        'selected_funds': selected_funds,
        'selected_fund_objects': selected_fund_objects,
        'selected_rounds': selected_rounds,
        'selected_round_objects': selected_round_objects,
        'selected_leads': selected_leads,
        'selected_reviewers': selected_reviewers,
        'selected_meta_terms': selected_meta_terms,
        'selected_category_options': selected_category_options,
        'status_counts': status_counts,
        'sort_options': sort_options,
        'selected_sort': selected_sort,
        'selected_statuses': selected_statuses,
        'is_filtered': is_filtered,
        'duration': end - start,
        'show_archive': is_user_has_access_to_view_archived_submissions(request.user),
    }
    return render(request, template_name, ctx)
