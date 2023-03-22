import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django_tables2 import RequestConfig
from wagtail.models import Page

from hypha.apply.funds.workflow import PHASES

from .models import (
    ApplicationSubmission,
    RoundsAndLabs,
)
from .permissions import is_user_has_access_to_view_archived_submissions
from .tables import (
    AdminSubmissionsTable,
    SubmissionFilter,
)

User = get_user_model()


def submission_dashboard(request: HttpRequest, template_name='submissions/all.html') -> HttpResponse:
    search_term = request.GET.get('query')
    show_archived = request.GET.get("archived", False) == 'on'
    selected_funds = request.GET.getlist("fund")
    selected_rounds = request.GET.getlist("round")
    selected_statuses = request.GET.getlist("status")

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

    if selected_statuses:
        qs = qs.filter(status__in=selected_statuses)

    status_count_raw = {}
    # year_counts_raw = {}
    # month_counts_raw = {}

    # Status Filter Options
    STATUS_DISPLAY_MAP = {k: v for k, v in PHASES}
    for row in qs.order_by().values('status').annotate(
        n=models.Count('status')
    ):
        status_count_raw[row['status']] = {
            'count': status_count_raw.get(row['status'], 0) + row['n'],
            'title': STATUS_DISPLAY_MAP[row['status']],
            'selected': row['status'] in selected_statuses,
        }

    status_counts = sorted(
        [
            {'slug': status, 'n': value['count'], 'title': value['title'], 'selected': value['selected']}
            for status, value in status_count_raw.items()
        ],
        key=lambda t: (t['selected'], t['n']), reverse=True
    )

    filter_kwargs = {**request.GET, **filter_extras}
    filters = SubmissionFilter(filter_kwargs, queryset=qs)
    is_filtered = (
        search_term or selected_funds or selected_statuses or selected_rounds
    )

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
        'show_archived': show_archived,
        'selected_funds': selected_funds,
        'selected_rounds': selected_rounds,
        'status_counts': status_counts,
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


def sub_menu_funds(request):
    selected_funds = request.GET.getlist("fund")

    # Funds Filter Options
    funds = [{
        'id': f.id,
        'selected': str(f.id) in selected_funds,
        'title': f.title
    } for f in Page.objects.filter(
        applicationsubmission__isnull=False
    ).order_by("title").distinct()]

    ctx = {
        'funds': funds,
        'selected_funds': selected_funds,
    }

    return render(request, "submissions/submenu/funds.html", ctx)


def sub_menu_leads(request):
    selected_leads = request.GET.getlist("lead")

    leads = [{
        'id': item.id,
        'selected': str(item.id) in selected_leads,
        'title': str(item)
    } for item in User.objects.filter(
        submission_lead__isnull=False
    ).order_by().distinct()]

    ctx = {
        'leads': leads,
        'selected_leads': selected_leads,
    }

    return render(request, "submissions/submenu/leads.html", ctx)


def sub_menu_rounds(request):
    selected_rounds = request.GET.getlist("round")
    qs = RoundsAndLabs.objects.all()

    open_rounds = [{
        'id': item.id,
        'selected': str(item.id) in selected_rounds,
        # 'open': item.is_open,
        'title': str(item)
    } for item in qs.open().filter(
        submissions__isnull=False
    ).order_by('-end_date').distinct()]

    closed_rounds = [{
        'id': item.id,
        'selected': str(item.id) in selected_rounds,
        # 'open': item.is_open,
        'title': str(item)
    } for item in qs.closed().filter(
        submissions__isnull=False
    ).order_by('-end_date').distinct()]

    ctx = {
        'open_rounds': open_rounds,
        'closed_rounds': closed_rounds,
        'selected_rounds': selected_rounds,
    }

    return render(request, "submissions/submenu/rounds.html", ctx)
