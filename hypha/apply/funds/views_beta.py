import time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from wagtail.models import Page

from hypha.apply.determinations.views import BatchDeterminationCreateView
from hypha.apply.funds.workflow import PHASES, get_action_mapping
from hypha.apply.search.filters import apply_date_filter
from hypha.apply.search.query_parser import parse_search_query
from hypha.apply.users.decorators import is_apply_staff

from . import permissions, services
from .models import (
    ApplicationSubmission,
    Round,
)
from .tables import (
    SubmissionFilter,
)

User = get_user_model()


@login_required
@user_passes_test(is_apply_staff)
def submission_all_beta(
    request: HttpRequest, template_name='submissions/all.html'
) -> HttpResponse:
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

    can_view_archives = permissions.can_access_archived_submissions(request.user)

    selected_fund_objects = (
        Page.objects.filter(id__in=selected_funds) if selected_funds else []
    )
    selected_round_objects = (
        Round.objects.filter(id__in=selected_rounds) if selected_rounds else []
    )

    if request.htmx:
        base_template = "includes/_partial-main.html"
    else:
        base_template = "funds/base_submissions_table.html"

    start = time.time()

    if can_view_archives and show_archived:
        qs = ApplicationSubmission.objects.include_archive().for_table(request.user)
    else:
        qs = ApplicationSubmission.objects.current().for_table(request.user)

    if not permissions.can_access_drafts(request.user):
        qs = qs.exclude_draft()

    match search_filters:
        case {'submitted': values}:
            qs = apply_date_filter(qs=qs, field='submit_time', values=values)
        case {'updated': values}:
            qs = apply_date_filter(qs=qs, field='last_update', values=values)
        case {'flagged': ['@me']}:
            qs = qs.flagged_by(request.user)
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

    status_count_raw = {}
    # year_counts_raw = {}
    # month_counts_raw = {}

    # Status Filter Options
    STATUS_MAP = dict(PHASES)
    for row in qs.order_by().values('status').annotate(n=models.Count('status')):
        phase = STATUS_MAP[row['status']]
        display_name = phase.display_name
        try:
            count = status_count_raw[display_name]['count']
        except KeyError:
            count = 0
        status_count_raw[display_name] = {
            'count': count + row['n'],
            'title': display_name,
            'bg_color': phase.bg_color,
            'slug': phase.display_slug,
            'selected': phase.display_slug in selected_statuses,
        }

    status_counts = sorted(
        status_count_raw.values(),
        key=lambda t: (t['selected'], t['count']),
        reverse=True,
    )

    filter_kwargs = {**request.GET, **filter_extras}
    filters = SubmissionFilter(filter_kwargs, queryset=qs)
    is_filtered = any(
        [
            selected_fund_objects,
            selected_statuses,
            selected_round_objects,
            selected_leads,
            selected_reviewers,
            selected_meta_terms,
            selected_category_options,
            selected_sort,
        ]
    )

    qs = filters.qs
    qs = qs.prefetch_related('meta_terms')

    sort_options_raw = {
        "submitted-desc": ("-submit_time", _('Newest')),
        "submitted-asc": ("submit_time", _('Oldest')),
        "comments-desc": ("-comment_count", _('Most Commented')),
        "comments-asc": ("comment_count", _('Least Commented')),
        "updated-desc": ("-last_update", _('Recently Updated')),
        "updated-asc": ("last_update", _('Least Recently Updated')),
        "relevance-desc": ("-rank", _('Best Match')),
    }

    sort_options = [
        {'name': v[1], 'param': k, 'selected': selected_sort == k}
        for k, v in sort_options_raw.items()
    ]

    if selected_sort and selected_sort in sort_options_raw.keys():
        if not search_query and selected_sort == 'relevance-desc':
            qs = qs.order_by('-submit_time')
        else:
            qs = qs.order_by(sort_options_raw[selected_sort][0])
    elif search_term:
        qs = qs.order_by('-rank')
    else:
        qs = qs.order_by("-last_update")

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
        'can_view_archive': can_view_archives,
        'can_bulk_archive': permissions.can_bulk_archive_submissions(request.user),
        'can_bulk_delete': permissions.can_bulk_delete_submissions(request.user),
    }
    return render(request, template_name, ctx)


@login_required
@require_http_methods(["POST"])
def bulk_archive_submissions(request):

    if not permissions.can_bulk_archive_submissions(request.user):
        return HttpResponseForbidden()

    submission_ids = request.POST.getlist("selectedSubmissionIds")
    submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)

    services.bulk_archive_submissions(
        submissions=submissions,
        user=request.user,
        request=request,
    )

    return HttpResponseClientRefresh()


@login_required
@require_http_methods(["POST"])
def bulk_delete_submissions(request):

    if not permissions.can_bulk_delete_submissions(request.user):
        return HttpResponseForbidden()

    submission_ids = request.POST.getlist("selectedSubmissionIds")
    submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)

    services.bulk_delete_submissions(
        submissions=submissions,
        user=request.user,
        request=request,
    )

    return HttpResponseClientRefresh()


@login_required
@user_passes_test(is_apply_staff)
@require_http_methods(["POST"])
def bulk_update_submissions_status(request: HttpRequest) -> HttpResponse:
    submission_ids = request.POST.getlist('selectedSubmissionIds')
    action = request.GET.get('action')
    transitions = get_action_mapping(workflow=None)[action]['transitions']

    qs = ApplicationSubmission.objects.filter(id__in=submission_ids)

    redirect: HttpResponse = BatchDeterminationCreateView.should_redirect(request, qs, transitions) # type: ignore
    if redirect:
        return HttpResponseClientRedirect(redirect.url)

    for submission in qs:
        submission.perform_transition(action, request.user, request=request)

    return HttpResponseClientRefresh()

