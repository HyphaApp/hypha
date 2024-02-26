import functools
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.decorators.http import require_GET, require_http_methods
from django_htmx.http import (
    HttpResponseClientRefresh,
)
from wagtail.models import Page

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)
from hypha.apply.categories.models import MetaTerm, Option
from hypha.apply.funds.forms import BatchUpdateReviewersForm
from hypha.apply.funds.models.reviewer_role import ReviewerRole
from hypha.apply.funds.permissions import has_permission
from hypha.apply.funds.reviewers.services import get_all_reviewers
from hypha.apply.funds.services import annotate_review_recommendation_and_count
from hypha.apply.users.groups import REVIEWER_GROUP_NAME

from . import services
from .models import ApplicationSubmission, Round
from .permissions import can_change_external_reviewers
from .utils import get_statuses_as_params, status_and_phases_mapping
from .workflow import PHASES_MAPPING

User = get_user_model()


@login_required
@require_http_methods(["GET"])
def sub_menu_funds(request):
    selected_funds = request.GET.getlist("fund")

    # Funds Filter Options
    funds = [
        {"id": f.id, "selected": str(f.id) in selected_funds, "title": f.title}
        for f in Page.objects.filter(applicationsubmission__isnull=False)
        .order_by("title")
        .distinct()
    ]

    ctx = {
        "funds": funds,
        "selected_funds": selected_funds,
    }

    return render(request, "submissions/submenu/funds.html", ctx)


@login_required
@require_http_methods(["GET"])
def sub_menu_leads(
    request, template_name="submissions/submenu/leads.html"
) -> HttpResponse:
    selected_leads = request.GET.getlist("lead")

    leads = [
        {
            "id": item.id,
            "selected": str(item.id) in selected_leads,
            "title": str(item),
            "slack": item.slack,
        }
        for item in User.objects.filter(submission_lead__isnull=False)
        .order_by()
        .distinct()
    ]

    # show selected and current user first
    leads = sorted(
        leads,
        key=lambda x: (not x["selected"], x["id"] != request.user.id, x["title"]),
        reverse=False,
    )

    ctx = {
        "leads": leads,
        "selected_leads": selected_leads,
    }

    return render(request, template_name, ctx)


@login_required
@require_http_methods(["GET"])
def sub_menu_rounds(request):
    selected_rounds = request.GET.getlist("round")
    selected_fund = request.GET.get("fund")
    qs = Round.objects.all()

    if selected_fund:
        fund = Page.objects.get(id=selected_fund)
        qs = Round.objects.child_of(fund)

    open_rounds = [
        {"id": item.id, "selected": str(item.id) in selected_rounds, "title": str(item)}
        for item in qs.open().order_by("-end_date").distinct()
    ]

    closed_rounds = [
        {"id": item.id, "selected": str(item.id) in selected_rounds, "title": str(item)}
        for item in qs.closed()
        .filter(submissions__isnull=False)
        .order_by("-end_date")
        .distinct()
    ]

    ctx = {
        "open_rounds": open_rounds,
        "closed_rounds": closed_rounds,
        "selected_rounds": selected_rounds,
    }

    return render(request, "submissions/submenu/rounds.html", ctx)


@login_required
@require_http_methods(["GET"])
def sub_menu_reviewers(request):
    selected_reviewers = request.GET.getlist("reviewers")
    qs = get_all_reviewers()

    reviewers = [
        {
            "id": item.id,
            "selected": str(item.id) in selected_reviewers,
            "title": str(item),
            "slack": item.slack,
        }
        for item in qs.order_by().distinct()
    ]

    # show selected and current user first
    reviewers = sorted(
        reviewers,
        key=lambda t: t["selected"] or t["id"] == request.user.id,
        reverse=True,
    )

    ctx = {
        "reviewers": reviewers,
        "selected_reviewers": selected_reviewers,
    }

    return render(request, "submissions/submenu/reviewers.html", ctx)


@login_required
@require_http_methods(["GET"])
def sub_menu_meta_terms(request):
    selected_meta_terms = request.GET.getlist("meta_terms")

    terms_qs = MetaTerm.objects.filter(
        filter_on_dashboard=True,
        id__in=ApplicationSubmission.objects.all()
        .values("meta_terms__id")
        .distinct("meta_terms__id"),
    ).exclude(depth=1)

    meta_terms = [
        {
            "id": item.id,
            "selected": str(item.id) in selected_meta_terms,
            "title": str(item),
            "depth_range": range((item.depth - 2) * 2),
            "depth": item.depth - 1,
        }
        for item in terms_qs
    ]

    ctx = {
        "meta_terms": meta_terms,
        "selected_meta_terms": selected_meta_terms,
    }

    return render(request, "submissions/submenu/meta-terms.html", ctx)


@login_required
@require_http_methods(["GET"])
def sub_menu_category_options(request):
    selected_category_options = request.GET.getlist("category_options")

    qs = Option.objects.filter(category__filter_on_dashboard=True).values("id", "value")

    items = [
        {
            "id": item["id"],
            "selected": str(item["id"]) in selected_category_options,
            "title": item["value"],
        }
        for item in qs
    ]

    items = sorted(items, key=lambda t: t["selected"], reverse=True)

    ctx = {
        "category_options": items,
        "selected_category_options": selected_category_options,
    }

    return render(request, "submissions/submenu/category.html", ctx)


@login_required
@require_http_methods(["GET"])
def partial_submission_activities(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    has_permission(
        "submission_view", request.user, object=submission, raise_exception=True
    )
    ctx = {"actions": get_related_actions_for_user(submission, request.user)}
    return render(request, "activity/include/action_list.html", ctx)


@login_required
@require_http_methods(["GET"])
def partial_reviews_card(request: HttpRequest, pk: str) -> HttpResponse:
    """Returns a partial html for the submission reviews box on the submission
    detail page and hovercard on the submissison list page.

    Args:
        request: HttpRequest object
        pk: Submission ID

    Returns:
        HttpResponse
    """
    submission = get_object_or_404(ApplicationSubmission, pk=pk)

    assigned_reviewers = submission.assigned.review_order()

    if not submission.stage.has_external_review:
        assigned_reviewers = assigned_reviewers.staff()

    # Calculate the recommendation based on role and staff reviews
    recommendation = submission.reviews.by_staff().recommendation()

    ctx = {
        "hidden_types": [REVIEWER_GROUP_NAME],
        "staff_reviewers_exist": assigned_reviewers.staff().exists(),
        "assigned_reviewers": assigned_reviewers,
        "recommendation": recommendation,
    }

    return render(request, "funds/includes/review_sidebar.html", ctx)


@login_required
@require_http_methods(["GET"])
def partial_reviews_decisions(request: HttpRequest) -> HttpResponse:
    submission_ids = request.GET.get("ids")
    if submission_ids:
        submission_ids = [x for x in submission_ids.split(",") if x]

    qs = ApplicationSubmission.objects.filter(id__in=submission_ids)
    qs = annotate_review_recommendation_and_count(qs)

    ctx = {
        "submissions": qs,
    }

    return render(
        request, "submissions/partials/submission-reviews-list-multi.html", ctx
    )


@login_required
@require_http_methods(["GET", "POST"])
def sub_menu_update_status(request: HttpRequest) -> HttpResponse:
    submission_ids = request.GET.getlist("selectedSubmissionIds")
    qs = ApplicationSubmission.objects.filter(id__in=submission_ids)

    list_of_actions_list = [s.get_actions_for_user(request.user) for s in qs]
    action_names = [[x[1] for x in action_list] for action_list in list_of_actions_list]
    common_actions = (
        sorted(functools.reduce(lambda l1, l2: set(l1).intersection(l2), action_names))
        if action_names
        else []
    )

    ctx = {
        "statuses": {slugify(a): a for a in common_actions}.items(),
    }

    return render(request, "submissions/submenu/change-status.html", ctx)


@login_required
@require_http_methods(["GET", "POST"])
def sub_menu_bulk_update_lead(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        submission_ids = request.POST.getlist("selectedSubmissionIds")
        lead = request.POST.get("lead")

        submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)
        lead = User.objects.get(id=lead)

        services.bulk_update_lead(
            submissions=submissions, user=request.user, request=request, lead=lead
        )
        return HttpResponseClientRefresh()

    leads = [
        {
            "id": item.id,
            "title": str(item),
            "slack": item.slack,
        }
        for item in User.objects.staff()
    ]

    # sort by lead names and put current user first
    leads = sorted(
        leads,
        key=lambda x: (x["id"] != request.user.id, x["title"]),
        reverse=False,
    )

    ctx = {
        "leads": leads,
    }

    return render(request, "submissions/submenu/bulk-update-lead.html", ctx)


@login_required
@require_http_methods(["GET", "POST"])
def sub_menu_bulk_update_reviewers(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        submission_ids = request.POST.getlist("selectedSubmissionIds")
        submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)
        external_reviewers_ids = request.POST.getlist("external_reviewers")
        external_reviewers = User.objects.filter(id__in=external_reviewers_ids)

        assigned_roles = {}
        for field, value in request.POST.items():
            if field.startswith("role_reviewer_"):
                if value:
                    role = ReviewerRole.objects.get(id=field[14:])
                    user = User.objects.staff().get(id=value)
                    # key, value of role id and reviewer id
                    assigned_roles[role] = user

        services.bulk_update_reviewers(
            submissions=submissions,
            user=request.user,
            request=request,
            external_reviewers=external_reviewers,
            assigned_roles=assigned_roles,
        )
        return HttpResponseClientRefresh()

    submission_ids = request.GET.getlist("selectedSubmissionIds")
    form = BatchUpdateReviewersForm(user=request.user)

    show_external_reviewers = False
    if submission_ids:
        submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)
        show_external_reviewers = all(
            can_change_external_reviewers(user=request.user, submission=s)
            for s in submissions
        )

    ctx = {
        "form": form,
        "show_external_reviewers": show_external_reviewers,
    }

    return render(request, "submissions/submenu/bulk-update-reviewers.html", ctx)


@login_required
@require_GET
def get_applications_status_counts(request):
    current_url = request.headers.get("Hx-Current-Url")
    current_url_queries = parse_qs(urlparse(current_url).query)
    application_status_url_query = current_url_queries.get("status")
    status_counts = dict(
        ApplicationSubmission.objects.current()
        .values("status")
        .annotate(
            count=Count("status"),
        )
        .values_list("status", "count")
    )

    grouped_statuses = {
        status: {
            "name": data["name"],
            "count": sum(status_counts.get(status, 0) for status in data["statuses"]),
            "url": reverse_lazy("funds:submissions:list")
            + get_statuses_as_params(status_and_phases_mapping[status]),
            "is_active": True
            if application_status_url_query
            and status_and_phases_mapping[status] == application_status_url_query
            else False,
        }
        for status, data in PHASES_MAPPING.items()
    }
    return render(
        request,
        "funds/includes/status-block.html",
        {
            "status_counts": grouped_statuses,
            "type": "Applications",
        },
    )
