from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, When
from django.shortcuts import render
from django.views.decorators.http import require_GET

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.workflow import active_statuses
from hypha.apply.projects.models import Project


def my_active_submissions(user):
    active_subs = (
        ApplicationSubmission.objects.filter(
            user=user,
        )
        .annotate(
            is_active=Case(When(status__in=active_statuses, then=True), default=False)
        )
        .select_related("draft_revision")
        .order_by("-is_active", "-submit_time")
    )
    for submission in active_subs:
        yield submission.from_draft()


@login_required
@require_GET
def applicant_submissions(request):
    active_submissions = list(my_active_submissions(request.user))

    page = request.GET.get("page", 1)
    page = Paginator(active_submissions, per_page=5, orphans=3).page(page)
    return render(
        request,
        template_name="dashboard/partials/applicant_submissions.html",
        context={"page": page},
    )


@login_required
@require_GET
def applicant_projects(request):
    active_projects = Project.objects.filter(user=request.user).order_by("-created_at")
    page = request.GET.get("page", 1)
    page = Paginator(active_projects, per_page=5, orphans=3).page(page)
    return render(
        request,
        template_name="dashboard/partials/applicant_projects.html",
        context={"page": page},
    )
