from urllib.parse import parse_qs, urlparse

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)
from hypha.apply.funds.utils import get_applications_status_counts

from ..models.project import Project
from ..permissions import has_permission
from ..utils import get_invoices_status_counts, get_project_status_counts


@login_required
@require_GET
def partial_project_activities(request, pk):
    project = get_object_or_404(Project, pk=pk)
    has_permission("project_access", request.user, object=project, raise_exception=True)
    ctx = {"actions": get_related_actions_for_user(project, request.user)}
    return render(request, "activity/include/action_list.html", ctx)


def get_status_counts(request, type):
    current_url = request.headers.get("Hx-Current-Url")
    current_url_queries = parse_qs(urlparse(current_url).query)
    if type == "projects":
        status_counts = get_project_status_counts(current_url_queries)
    elif type == "invoices":
        status_counts = get_invoices_status_counts(current_url_queries)
    elif type == "applications":
        status_counts = get_applications_status_counts(current_url_queries)
    else:
        status_counts = {}

    return render(
        request,
        "funds/includes/status-block.html",
        {
            "status_counts": status_counts,
            "type": type,
        },
    )
