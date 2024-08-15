from django.contrib.contenttypes.models import ContentType

from .models import Task
from .options import (
    INVOICE_REQUIRED_CHANGES,
    INVOICE_WAITING_APPROVAL,
    PAF_REQUIRED_CHANGES,
    PROJECT_SUBMIT_PAF,
    PROJECT_WAITING_CONTRACT,
    PROJECT_WAITING_CONTRACT_REVIEW,
    PROJECT_WAITING_PAF,
)

project_lead_task_codes = [
    PROJECT_WAITING_PAF,
    PROJECT_SUBMIT_PAF,
    PAF_REQUIRED_CHANGES,
    PROJECT_WAITING_CONTRACT,
    PROJECT_WAITING_CONTRACT_REVIEW,
    INVOICE_REQUIRED_CHANGES,
    INVOICE_WAITING_APPROVAL,
]


def get_project_lead_tasks(lead, related_obj):
    tasks = Task.objects.filter(
        code__in=project_lead_task_codes,
        user=lead,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    )
    return tasks
