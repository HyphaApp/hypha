from django.conf import settings

from .models import Deliverable, Project


def fetch_and_save_deliverables(project_id, program_project_id=''):
    """
    Get deliverables from various third party integrations.
    """
    if settings.INITIALISE_INTACCT:
        from hypha.apply.projects.services.sageintacct.utils import fetch_deliverables
        deliverables = fetch_deliverables(program_project_id)
        save_deliverables(project_id, deliverables)


def save_deliverables(project_id, deliverables=[]):
    project = Project.objects.get(id=project_id)

    deliverable_list = []
    for deliverable in deliverables:
        deliverable_list.append(
            Deliverable(
                name=deliverable['ITEMNAME'],
                available_to_invoice=int(float(deliverable['QTY_REMAINING'])),
                unit_price=deliverable['PRICE'],
                project=project
            )
        )

    Deliverable.objects.bulk_create(deliverable_list)
