import functools
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from django_htmx.http import (
    HttpResponseClientRefresh,
)
from wagtail.models import Page

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.categories.models import MetaTerm, Option
from hypha.apply.funds.forms import BatchUpdateReviewersForm
from hypha.apply.funds.models.reviewer_role import ReviewerRole
from hypha.apply.funds.models.screening import ScreeningStatus
from hypha.apply.funds.models.utils import (
    STATUS_ERROR,
    STATUS_GENERATING,
    STATUS_SUCCESS,
    SubmissionExportManager,
)
from hypha.apply.funds.permissions import has_permission
from hypha.apply.funds.reviewers.services import get_all_reviewers
from hypha.apply.funds.services import annotate_review_recommendation_and_count
from hypha.apply.review.options import REVIEWER
from hypha.apply.todo.options import DOWNLOAD_SUBMISSIONS_EXPORT
from hypha.apply.todo.views import remove_tasks_of_related_obj_for_specific_code
from hypha.apply.users.roles import REVIEWER_GROUP_NAME

from .. import services
from ..models import ApplicationSubmission, Round
from ..permissions import can_change_external_reviewers
from ..utils import (
    check_submissions_same_determination_form,
    get_export_polling_time,
    get_or_create_default_screening_statuses,
)
from ..workflows.constants import DETERMINATION_OUTCOMES

User = get_user_model()


@login_required
def partial_submission_lead(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    return render(
        request, "submissions/partials/submission-lead.html", {"submission": submission}
    )


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

    if not request.user.is_org_faculty and request.user.is_reviewer:
        # Only show external reviewers info on reviews that have visibility set to REVIEWER
        assigned_reviewers = assigned_reviewers.filter(
            Q(review__visibility=REVIEWER) | Q(reviewer=request.user)
        )
        recommendation = (
            submission.reviews.by_staff().filter(visibility=REVIEWER).recommendation()
        )
    else:
        recommendation = submission.reviews.by_staff().recommendation()
        if not submission.stage.has_external_review:
            assigned_reviewers = assigned_reviewers.staff()

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
def partial_meta_terms_card(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    meta_terms = submission.meta_terms.all()
    ctx = {"meta_terms": meta_terms, "submission": submission}
    return render(request, "submissions/partials/meta-terms-card.html", ctx)


@login_required
@require_http_methods(["GET", "POST"])
def sub_menu_update_status(request: HttpRequest) -> HttpResponse:
    submission_ids = request.GET.getlist("selectedSubmissionIds")
    qs = ApplicationSubmission.objects.filter(id__in=submission_ids)

    allow_determination = check_submissions_same_determination_form(qs)

    list_of_actions_list = [s.get_actions_for_user(request.user) for s in qs]

    action_names = [
        [
            action[1]
            for action in action_list
            if allow_determination or action[0] not in DETERMINATION_OUTCOMES
        ]
        for action_list in list_of_actions_list
    ]

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
@require_http_methods(["GET"])
def partial_submission_answers(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)
    has_permission(
        "submission_view", request.user, object=submission, raise_exception=True
    )
    return render(
        request,
        "funds/includes/rendered_answers.html",
        {"object": submission},
    )


@login_required
def partial_screening_card(request, pk):
    submission = get_object_or_404(ApplicationSubmission, pk=pk)

    view_permission, _ = has_permission(
        "can_view_submission_screening", request.user, submission, raise_exception=False
    )
    can_edit, _ = has_permission(
        "submission_action", request.user, submission, raise_exception=False
    )

    if not view_permission:
        return HttpResponse(status=204)

    if can_edit and request.method == "POST":
        action = request.POST.get("action")
        old_status_str = str(submission.get_current_screening_status() or "-")
        if action and action.isdigit():
            submission.screening_statuses.clear()
            screening_status = ScreeningStatus.objects.get(id=action)
            submission.screening_statuses.add(screening_status)
        elif action == "clear":
            submission.screening_statuses.clear()

        # Record activity
        messenger(
            MESSAGES.SCREENING,
            request=request,
            user=request.user,
            source=submission,
            related=old_status_str,
        )

    yes_screening_statuses = ScreeningStatus.objects.filter(yes=True)
    no_screening_statuses = ScreeningStatus.objects.filter(yes=False)

    if not yes_screening_statuses or not no_screening_statuses:
        return HttpResponse(status=204)

    default_yes, default_no = get_or_create_default_screening_statuses(
        yes_screening_statuses, no_screening_statuses
    )

    ctx = {
        "default_yes": default_yes,
        "default_no": default_no,
        "object": submission,
        "can_screen": can_edit,
        "current_yes": submission.screening_statuses.filter(yes=True).first(),
        "current_no": submission.screening_statuses.filter(yes=False).first(),
        "yes_screening_options": yes_screening_statuses,
        "no_screening_options": no_screening_statuses,
    }
    return render(request, "funds/includes/screening_status_block.html", ctx)


def submission_export_status(request: HttpRequest) -> HttpResponse:
    """The partial to get the status of a bulk submission export task"""
    ctx = {}
    status = None

    if not settings.CELERY_TASK_ALWAYS_EAGER:
        if export_manager := SubmissionExportManager.objects.filter(
            user=request.user
        ).first():
            # If there's an existing/active export, show it's status
            status = export_manager.status
            if status == STATUS_GENERATING:
                ctx["poll_time"] = get_export_polling_time(export_manager.total_export)
    else:
        ctx["not_async"] = True

    if status is None or status == STATUS_ERROR:
        # There's not an active job or we're running in sync, extract all submissions
        # view URL to pass the query params to the `submissions_all` view for
        # generation, appending `&format=csv`
        all_url = urlparse(request.headers.get("Hx-Current-Url"))
        url_list = list(all_url)
        url_list[4] = urlencode(
            {**parse_qs(all_url.query), "format": "csv"}, doseq=True
        )
        ctx["start_export_url"] = urlunparse(url_list)

    ctx["generating"] = status == STATUS_GENERATING
    ctx["failed"] = status == STATUS_ERROR
    ctx["success"] = status == STATUS_SUCCESS

    return render(request, "submissions/partials/export-submission-button.html", ctx)


def submission_export_download(request: HttpRequest) -> HttpResponse:
    export_manager = get_object_or_404(SubmissionExportManager, user=request.user)
    if export_manager.status == "success":
        response = HttpResponse(export_manager.export_data, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=submissions.csv"

        remove_tasks_of_related_obj_for_specific_code(
            code=DOWNLOAD_SUBMISSIONS_EXPORT, related_obj=export_manager
        )
        export_manager.delete()

        return response

    raise Http404()
