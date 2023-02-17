import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_tables2 import RequestConfig

from .models import (
    ApplicationSubmission,
)
from .permissions import is_user_has_access_to_view_archived_submissions
from .tables import (
    AdminSubmissionsTable,
    SubmissionFilterAndSearch,
)

User = get_user_model()


def submission_dashboard(request: HttpRequest, template_name='submissions/all.html') -> HttpResponse:
    search_term = request.GET.get('query')
    show_archived = request.GET.get("archived", False)

    if request.htmx:
        base_template = "includes/_partial-main.html"
    else:
        base_template = "funds/base_submissions_table.html"

    start = time.time()

    if show_archived == "1":
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

    status_counts_raw = {}
    # tag_counts_raw = {}
    # year_counts_raw = {}
    # month_counts_raw = {}

    filter_kwargs = {**request.GET, **filter_extras}
    filters = SubmissionFilterAndSearch(filter_kwargs, queryset=qs)

    qs = filters.qs

    if search_term:
        qs = qs.order_by('-rank')

    table = AdminSubmissionsTable(data=qs)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)

    end = time.time()

    ctx = {
        'base_template': base_template,
        'search_term': search_term,
        'filters': filters,
        'table': table,
        'duration': end - start,
        'total': len(table.rows),
        'show_archive': is_user_has_access_to_view_archived_submissions(request.user),
    }
    return render(request, template_name, ctx)


# submission_all_beta = SubmissionAdminListView.as_view()
submission_all_beta = submission_dashboard
