import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django_tables2 import RequestConfig

from hypha.apply.funds.workflow import PHASES

from .models import (
    ApplicationSubmission,
)
from .permissions import is_user_has_access_to_view_archived_submissions
from .tables import (
    AdminSubmissionsTable,
    SubmissionFilter,
)

User = get_user_model()


@login_required
def submission_dashboard(request: HttpRequest, template_name='submissions/all.html') -> HttpResponse:
    search_term = request.GET.get('query')
    show_archived = request.GET.get("archived", False) == 'on'
    selected_funds = request.GET.getlist("fund")
    selected_rounds = request.GET.getlist("round")
    selected_leads = request.GET.getlist("lead")
    selected_statuses = request.GET.getlist("status")
    selected_reviewers = request.GET.getlist("reviewers")
    selected_sort = request.GET.get("sort")
    # per_page = request.GET.get("per_page", 20)

    if request.htmx:
        base_template = "includes/_partial-main.html"
    else:
        base_template = "funds/base_submissions_table.html"

    start = time.time()

    if show_archived:
        qs = ApplicationSubmission.objects.include_archive().for_table(request.user)
    else:
        qs = ApplicationSubmission.objects.current().for_table(request.user)

    if search_term:
        query = SearchQuery(search_term)
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
            'selected': status_display in selected_statuses,
        }

    status_counts = sorted(
        status_count_raw.values(),
        key=lambda t: (t['selected'], t['count']), reverse=True
    )

    filter_kwargs = {**request.GET, **filter_extras}
    filters = SubmissionFilter(filter_kwargs, queryset=qs)
    is_filtered = any([
        search_term,
        selected_funds,
        selected_statuses,
        selected_rounds,
        selected_leads,
        selected_reviewers,
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
        if not search_term and selected_sort == 'relevance-desc':
            qs = qs.order_by('-submit_time')
        else:
            qs = qs.order_by(sort_options_raw[selected_sort][0])
    elif search_term:
        qs = qs.order_by('-rank')
    else:
        qs = qs.order_by("-submit_time")


    table = AdminSubmissionsTable(data=qs)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)

    end = time.time()

    ctx = {
        'base_template': base_template,
        'search_term': search_term,
        'filters': filters,
        'submissions': qs,
        'show_archived': show_archived,
        'selected_funds': selected_funds,
        'selected_rounds': selected_rounds,
        'selected_leads': selected_leads,
        'selected_reviewers': selected_reviewers,
        'status_counts': status_counts,
        'sort_options': sort_options,
        'selected_sort': selected_sort,
        'selected_statuses': selected_statuses,
        'is_filtered': is_filtered,
        'table': table,
        'duration': end - start,
        'total': len(table.rows),
        'show_archive': is_user_has_access_to_view_archived_submissions(request.user),
    }
    return render(request, template_name, ctx)


# submission_all_beta = SubmissionAdminListView.as_view()
submission_all_beta = submission_dashboard
