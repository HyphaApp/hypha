from django.conf import settings
from django.urls import reverse

from .models import Deliverable, Project


def get_paf_data_with_field(project):
    data_dict = {}
    form_data_dict = project.form_data
    for field in project.form_fields.raw_data:
        if field['id'] in form_data_dict.keys():
            if isinstance(field['value'], dict) and 'field_label' in field['value']:
                data_dict[field['value']['field_label']] = form_data_dict[field['id']]

    return data_dict


def get_supporting_documents(request, project):
    documents_dict = {}
    for packet_file in project.packet_files.all():
        documents_dict[packet_file.title] = request.build_absolute_uri(
            reverse('apply:projects:document', kwargs={'pk': project.id, 'file_pk': packet_file.id})
        )
    return documents_dict


def get_paf_download_context(request, project):
    context = {}
    context['id'] = project.id
    context['title'] = project.title
    context['project_link'] = request.build_absolute_uri(
        reverse('apply:projects:detail', kwargs={'pk': project.id})
    )
    context['proposed_start_date'] = project.proposed_start
    context['proposed_end_date'] = project.proposed_end
    context['contractor_name'] = project.vendor.contractor_name if project.vendor else None
    context['total_amount'] = project.value

    context['approvers'] = project.paf_reviews_meta_data
    context['paf_data'] = get_paf_data_with_field(project)
    context['submission'] = project.submission
    context['submission_link'] = request.build_absolute_uri(
        reverse('apply:submissions:detail', kwargs={'pk': project.submission.id})
    )
    context['supporting_documents'] = get_supporting_documents(request, project)
    context['org_name'] = settings.ORG_LONG_NAME
    return context


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


def save_deliverables(project_id, deliverables=[]):
    '''
    TODO: List of deliverables coming from IntAcct is
    not varified yet from the team. This method may need
    revision when that is done.
    '''
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
