from typing import List

from celery import shared_task
from django.conf import settings

from hypha.apply.projects.models.payment import InvoiceExportManager
from hypha.apply.projects.utils import export_invoices_to_csv
from hypha.apply.todo.options import (
    DOWNLOAD_INVOICES_EXPORT,
    FAILED_INVOICES_EXPORT,
)
from hypha.apply.todo.views import add_task_to_user
from hypha.apply.users.models import User


@shared_task
def generate_invoice_csv(qs_ids: List[int], request_user_id: int) -> None:
    """Celery task to generate a CSV file containing the given invoice IDs.

    Updates the user's InvoiceExportManager object with status/final data, then
    adds a download task to the user's `My Tasks` when completed.
    """
    try:
        from hypha.apply.projects.models.payment import Invoice

        qs = (
            Invoice.objects.filter(id__in=qs_ids)
            .select_related("project", "project__user")
            .prefetch_related("tags")
        )
        request_user = User.objects.get(pk=request_user_id)

        if current := InvoiceExportManager.objects.filter(user=request_user):
            current.delete()

        export_manager = InvoiceExportManager.objects.create(
            user=request_user, total_export=len(qs_ids)
        )
        export_manager.export_data = export_invoices_to_csv(qs.iterator())
        export_manager.set_completed_and_save()

        user_task = DOWNLOAD_INVOICES_EXPORT

    except Exception as exc:
        export_manager.set_failed_and_save()
        user_task = FAILED_INVOICES_EXPORT

        if settings.SENTRY_DSN:
            from sentry_sdk import capture_exception

            capture_exception(exc)
        else:
            raise exc
    finally:
        if not settings.CELERY_TASK_ALWAYS_EAGER:
            add_task_to_user(
                code=user_task,
                user=request_user,
                related_obj=export_manager,
            )
