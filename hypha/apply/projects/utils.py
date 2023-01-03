from django.conf import settings

from .models import Deliverable, Project


def fetch_and_save_deliverables(project_id):
    """
    Fetch deliverables from the enabled payment service and save it in Hypha.
    """
    if settings.INTACCT_ENABLED:
        from hypha.apply.projects.services.sageintacct.utils import fetch_deliverables
        project = Project.objects.get(id=project_id)
        program_project_id = project.program_project_id
        deliverables = fetch_deliverables(program_project_id)
        save_deliverables(project_id, deliverables)


def save_deliverables(project_id, deliverables=None):
    '''
    TODO: List of deliverables coming from IntAcct is
    not verified yet from the team. This method may need
    revision when that is done.
    '''
    if deliverables is None:
        deliverables = []
    if deliverables:
        remove_deliverables_from_project(project_id)
    project = Project.objects.get(id=project_id)
    new_deliverable_list = []
    for deliverable in deliverables:
        item_id = deliverable['ITEMID']
        item_name = deliverable['ITEMNAME']
        qty_remaining = int(float(deliverable['QTY_REMAINING']))
        price = deliverable['PRICE']
        extra_information = {
            'UNIT': deliverable['UNIT'],
            'DEPARTMENTID': deliverable['DEPARTMENTID'],
            'PROJECTID': deliverable['PROJECTID'],
            'LOCATIONID': deliverable['LOCATIONID'],
            'CLASSID': deliverable['CLASSID'],
            'BILLABLE': deliverable['BILLABLE'],
            'CUSTOMERID': deliverable['CUSTOMERID'],
        }
        new_deliverable_list.append(
            Deliverable(
                external_id=item_id,
                name=item_name,
                available_to_invoice=qty_remaining,
                unit_price=price,
                extra_information=extra_information,
                project=project
            )
        )
    Deliverable.objects.bulk_create(new_deliverable_list)


def remove_deliverables_from_project(project_id):
    project = Project.objects.get(id=project_id)
    deliverables = project.deliverables.all()
    for deliverable in deliverables:
        deliverable.project = None
        deliverable.save()


def fetch_and_save_project_details(project_id, external_projectid):
    '''
    Fetch and save project contract information from enabled payment service.
    '''
    if settings.INTACCT_ENABLED:
        from hypha.apply.projects.services.sageintacct.utils import (
            fetch_project_details,
        )
        data = fetch_project_details(external_projectid)
        save_project_details(project_id, data)


def save_project_details(project_id, data):
    project = Project.objects.get(id=project_id)
    project.external_project_information = data
    project.save()


def create_invoice(invoice):
    '''
    Creates invoice at enabled payment service.
    '''
    if settings.INTACCT_ENABLED:
        from hypha.apply.projects.services.sageintacct.utils import (
            create_intacct_invoice,
        )
        create_intacct_invoice(invoice)
