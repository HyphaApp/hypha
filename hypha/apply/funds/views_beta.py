import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django_htmx.http import HttpResponseClientRedirect, HttpResponseClientRefresh
from wagtail.models import Page

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.categories.models import Option
from hypha.apply.determinations.views import BatchDeterminationCreateView
from hypha.apply.funds.models.screening import ScreeningStatus
from hypha.apply.funds.workflow import PHASES, get_action_mapping, review_statuses
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


def screening_decision_context(selected_screening_statuses: list) -> dict:
    screening_options = [
        {
            "slug": "null",
            "title": _("No screening"),
            "selected": "null" in selected_screening_statuses,
        },
    ] + [
        {
            "slug": str(item.id),
            "title": item.title,
            "selected": str(item.id) in selected_screening_statuses,
        }
        for item in ScreeningStatus.objects.filter(
            id__in=ApplicationSubmission.objects.all()
            .values("screening_statuses__id")
            .distinct("screening_statuses__id")
        )
    ]

    selected_screening_statuses_objects = filter(
        lambda x: x["selected"] is True, screening_options
    )
    return {
        "selected_screening_statuses_objects": selected_screening_statuses_objects,
        "screening_options": screening_options,
    }


@login_required
@user_passes_test(is_apply_staff)
def submission_all_beta(
    request: HttpRequest, template_name="submissions/all.html"
) -> HttpResponse:
    search_query = request.GET.get("query") or ""
    parsed_query = parse_search_query(search_query)
    search_term, search_filters = parsed_query["text"], parsed_query["filters"]

    show_archived = request.GET.get("archived", False) == "on"
    selected_funds = request.GET.getlist("fund")
    selected_rounds = request.GET.getlist("round")
    selected_leads = request.GET.getlist("lead")
    selected_applicants = request.GET.getlist("applicants")
    selected_statuses = request.GET.getlist("status")
    selected_screening_statuses = request.GET.getlist("screening_statuses")
    selected_reviewers = request.GET.getlist("reviewers")
    selected_meta_terms = request.GET.getlist("meta_terms")
    selected_category_options = request.GET.getlist("category_options")
    selected_sort = request.GET.get("sort")
    page = request.GET.get("page", 1)

    can_view_archives = permissions.can_view_archived_submissions(request.user)

    selected_fund_objects = (
        Page.objects.filter(id__in=selected_funds) if selected_funds else []
    )
    selected_round_objects = (
        Round.objects.filter(id__in=selected_rounds) if selected_rounds else []
    )

    if request.htmx and not request.htmx.boosted:
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

    if "submitted" in search_filters:
        qs = apply_date_filter(
            qs=qs, field="submit_time", values=search_filters["submitted"]
        )

    if "updated" in search_filters:
        qs = apply_date_filter(
            qs=qs, field="last_update", values=search_filters["updated"]
        )

    if "flagged" in search_filters:
        if "@me" in search_filters["flagged"]:
            qs = qs.flagged_by(request.user)
        if "@staff" in search_filters["flagged"]:
            qs = qs.flagged_staff()

    if "lead" in search_filters:
        if "@me" in search_filters["lead"]:
            qs = qs.filter(lead=request.user)

    if "reviewer" in search_filters:
        if "@me" in search_filters["reviewer"]:
            qs = qs.filter(reviewers=request.user)

    if "id" in search_filters:
        qs = qs.filter(id__in=search_filters["id"])

    if "is" in search_filters:
        if "archived" in search_filters["is"]:
            qs = qs.filter(is_archive=True)

    if search_term:
        query = SearchQuery(search_term, search_type="websearch")
        rank_annotation = SearchRank(models.F("search_document"), query)
        qs = qs.filter(search_document=query)
        qs = qs.annotate(rank=rank_annotation)

    filter_extras = {
        "exclude": settings.SUBMISSIONS_TABLE_EXCLUDED_FIELDS,
    }

    if selected_funds:
        qs = qs.filter(page__in=selected_funds)

    if selected_applicants:
        qs = qs.filter(user__in=selected_applicants)

    status_count_raw = {}
    # year_counts_raw = {}
    # month_counts_raw = {}

    # Status Filter Options
    STATUS_MAP = dict(PHASES)
    for row in qs.order_by().values("status").annotate(n=models.Count("status")):
        phase = STATUS_MAP[row["status"]]
        display_name = phase.display_name
        try:
            count = status_count_raw[display_name]["count"]
        except KeyError:
            count = 0
        status_count_raw[display_name] = {
            "count": count + row["n"],
            "title": display_name,
            "bg_color": phase.bg_color,
            "slug": phase.display_slug,
            "selected": phase.display_slug in selected_statuses,
        }

    status_counts = sorted(
        status_count_raw.values(),
        key=lambda t: (t["selected"], t["count"]),
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
            selected_applicants,
            selected_reviewers,
            selected_meta_terms,
            selected_category_options,
            selected_screening_statuses,
            selected_sort,
        ]
    )

    qs = filters.qs
    qs = qs.prefetch_related("meta_terms")

    sort_options_raw = {
        "submitted-desc": ("-submit_time", _("Newest")),
        "submitted-asc": ("submit_time", _("Oldest")),
        "comments-desc": ("-comment_count", _("Most Commented")),
        "comments-asc": ("comment_count", _("Least Commented")),
        "updated-desc": ("-last_update", _("Recently Updated")),
        "updated-asc": ("last_update", _("Least Recently Updated")),
        "relevance-desc": ("-rank", _("Best Match")),
    }

    sort_options = [
        {"name": v[1], "param": k, "selected": selected_sort == k}
        for k, v in sort_options_raw.items()
    ]

    if selected_sort and selected_sort in sort_options_raw.keys():
        if not search_query and selected_sort == "relevance-desc":
            qs = qs.order_by("-submit_time")
        else:
            qs = qs.order_by(sort_options_raw[selected_sort][0])
    elif search_term:
        qs = qs.order_by("-rank")
    else:
        qs = qs.order_by("-submit_time")

    end = time.time()

    page = Paginator(qs, per_page=60, orphans=20).page(page)

    # Pair the category ID with it's respective label
    selected_category_options = Option.objects.filter(
        pk__in=selected_category_options
    ).values("id", "value")

    ctx = {
        "base_template": base_template,
        "search_query": search_query,
        "filters": filters,
        "page": page,
        "submissions": page.object_list,
        "submission_ids": [x.id for x in page.object_list],
        "show_archived": show_archived,
        "selected_funds": selected_funds,
        "selected_fund_objects": selected_fund_objects,
        "selected_rounds": selected_rounds,
        "selected_round_objects": selected_round_objects,
        "selected_leads": selected_leads,
        "selected_applicants": selected_applicants,
        "selected_reviewers": selected_reviewers,
        "selected_meta_terms": selected_meta_terms,
        "selected_category_options": selected_category_options,
        "status_counts": status_counts,
        "sort_options": sort_options,
        "selected_sort": selected_sort,
        "selected_statuses": selected_statuses,
        "is_filtered": is_filtered,
        "duration": end - start,
        "can_view_archive": can_view_archives,
        "can_bulk_archive": permissions.can_bulk_archive_submissions(request.user),
        "can_bulk_delete": permissions.can_bulk_delete_submissions(request.user),
    } | screening_decision_context(selected_screening_statuses)
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

    messages.info(request, f"{len(submissions)} submissions archived.")
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
    submission_ids = request.POST.getlist("selectedSubmissionIds")
    action = request.POST.get("action")

    transitions = get_action_mapping(workflow=None)[action]["transitions"]

    submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)

    redirect: HttpResponse = BatchDeterminationCreateView.should_redirect(
        request, submissions, transitions
    )
    if redirect:
        return HttpResponseClientRedirect(redirect.url)

    failed = []
    phase_changes = {}
    for submission in submissions:
        valid_actions = {
            action for action, _ in submission.get_actions_for_user(request.user)
        }
        old_phase = submission.phase
        try:
            transition = (valid_actions & set(transitions)).pop()
            submission.perform_transition(
                transition,
                request.user,
                request=request,
                notify=False,
            )
        except (PermissionDenied, KeyError):
            failed.append(submission)
        else:
            phase_changes[submission.id] = old_phase

    if failed:
        messages.warning(
            request,
            _("Failed to update: ")
            + ", ".join(str(submission) for submission in failed),
        )

    if succeeded_submissions := submissions.exclude(id__in=(s.id for s in failed)):
        messenger(
            MESSAGES.BATCH_TRANSITION,
            user=request.user,
            request=request,
            sources=succeeded_submissions,
            related=phase_changes,
        )

    if ready_for_review := filter(lambda phase: phase in review_statuses, transitions):
        messenger(
            MESSAGES.BATCH_READY_FOR_REVIEW,
            user=request.user,
            request=request,
            sources=succeeded_submissions.filter(status__in=ready_for_review),
        )

    return HttpResponseClientRefresh()
