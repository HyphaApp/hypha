from urllib.parse import parse_qs, urlparse

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET

from hypha.apply.activity.services import (
    get_related_actions_for_user,
)
from hypha.apply.funds.utils import get_statuses_as_params

from ..constants import statuses_and_table_statuses_mapping
from ..models.payment import Invoice
from ..models.project import PROJECT_STATUS_CHOICES, Project
from ..permissions import has_permission


@login_required
@require_GET
def partial_project_activities(request, pk):
    project = get_object_or_404(Project, pk=pk)
    has_permission("project_access", request.user, object=project, raise_exception=True)
    ctx = {"actions": get_related_actions_for_user(project, request.user)}
    return render(request, "activity/include/action_list.html", ctx)


@login_required
@require_GET
def get_project_status_counts(request):
    current_url = request.headers.get("Hx-Current-Url")
    current_url_queries = parse_qs(urlparse(current_url).query)
    project_status_url_query = current_url_queries.get("project_status")
    project_status_counts = dict(
        Project.objects.all()
        .values("status")
        .annotate(
            count=Count("status"),
        )
        .values_list(
            "status",
            "count",
        )
    )
    status_counts = {
        key: {
            "name": display.replace(" and ", " & "),
            "count": project_status_counts.get(key, 0),
            "url": reverse_lazy("funds:projects:all") + "?project_status=" + key,
            "is_active": True
            if project_status_url_query and key in project_status_url_query
            else False,
        }
        for key, display in PROJECT_STATUS_CHOICES
    }

    return render(
        request,
        "funds/includes/status-block.html",
        {
            "status_counts": status_counts,
            "type": "Projects",
        },
    )


@login_required
@require_GET
def get_invoices_status_counts(request):
    current_url = request.headers.get("Hx-Current-Url")
    current_url_queries = parse_qs(urlparse(current_url).query)
    invoice_status_url_query = current_url_queries.get("status")
    invoices_status_counts = dict(
        Invoice.objects.all()
        .values("status")
        .annotate(
            count=Count("status"),
        )
        .values_list(
            "status",
            "count",
        )
    )
    status_counts = {
        name: {
            "name": name,
            "count": sum(invoices_status_counts.get(status, 0) for status in statuses),
            "url": reverse_lazy("funds:projects:invoices")
            + get_statuses_as_params(statuses),
            "is_active": True
            if invoice_status_url_query and statuses == invoice_status_url_query
            else False,
        }
        for name, statuses in statuses_and_table_statuses_mapping.items()
    }
    return render(
        request,
        "funds/includes/status-block.html",
        {
            "status_counts": status_counts,
            "type": "Invoices",
        },
    )
