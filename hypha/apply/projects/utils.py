from .models import Project, Deliverable


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
