import logging
from datetime import timedelta

from django.conf import settings

from .sageintacctsdk import SageIntacctSDK


def fetch_deliverables(program_project_id=""):
    """
    Fetch deliverables from IntAcct using the program project id(DEPARTMENTID).

    Returns a list of deliverables or an empty list.

    Also logs any error that occurred during the API call.
    """
    if not program_project_id:
        return []
    formatted_filter = {
        "and": {
            "equalto": [
                {"field": "DOCPARID", "value": "Project Contract"},
                {"field": "DEPARTMENTID", "value": program_project_id},
            ],
            "greaterthan": {"field": "QTY_REMAINING", "value": 0.0},
        }
    }

    try:
        connection = SageIntacctSDK(
            sender_id=settings.INTACCT_SENDER_ID,
            sender_password=settings.INTACCT_SENDER_PASSWORD,
            user_id=settings.INTACCT_USER_ID,
            company_id=settings.INTACCT_COMPANY_ID,
            user_password=settings.INTACCT_USER_PASSWORD,
        )
    except Exception as e:
        logging.error(e)
        return []

    deliverables = connection.purchasing.get_by_query(filter_payload=formatted_filter)
    return deliverables


def get_deliverables_json(invoice):
    """
    Get a json format of deliverables attached to the invoice.

    Used when creating invoice in IntAcct.
    """
    deliverables = invoice.deliverables.all()
    deliverables_list = []
    for deliverable in deliverables:
        project_deliverable = deliverable.deliverable
        extra_info = project_deliverable.extra_information
        deliverables_list.append(
            {
                "itemid": project_deliverable.external_id,
                "quantity": deliverable.quantity,
                "unit": extra_info["UNIT"],
                "price": project_deliverable.unit_price,
                "locationid": extra_info["LOCATIONID"],
                "departmentid": extra_info["DEPARTMENTID"],
                "projectid": extra_info["PROJECTID"],
                "customerid": extra_info["CUSTOMERID"],
                "classid": extra_info["CLASSID"],
                "billable": extra_info["BILLABLE"],
            }
        )
    return deliverables_list


def create_intacct_invoice(invoice):
    """
    Creates a Contract Invoice Release at IntAcct.

    Note that the order of field send in the query is important.

    API call may also fail if the order of the field is not correct.
    """
    project = invoice.project
    external_project_information = project.external_project_information
    external_projectid = project.external_projectid
    transactiontype = "Contract Invoice Release"
    date_created = invoice.requested_at
    createdfrom = external_project_information["DOCPARID"] + "-" + external_projectid
    vendorid = external_project_information["CUSTVENDID"]
    referenceno = external_project_information["PONUMBER"]
    project.created_at + timedelta(days=20)
    datedue = date_created + timedelta(days=20)
    contract_start_date = project.proposed_start
    contract_end_date = project.proposed_end
    deliverables = get_deliverables_json(invoice)
    vendordocno = invoice.vendor_document_number
    data = {
        "transactiontype": transactiontype,
        "datecreated": {
            "year": date_created.year,
            "month": date_created.month,
            "day": date_created.day,
        },
        "createdfrom": createdfrom,
        "vendorid": vendorid,
        "referenceno": referenceno,
        "vendordocno": vendordocno,
        "datedue": {
            "year": datedue.year,
            "month": datedue.month,
            "day": datedue.day,
        },
        "returnto": {"contactname": ""},
        "payto": {"contactname": ""},
        "customfields": {
            "customfield": [
                {
                    "customfieldname": "CONTRACT_START_DATE",
                    "customfieldvalue": f"{contract_start_date.month}/{contract_start_date.day}/{contract_start_date.year}",
                },
                {
                    "customfieldname": "CONTRACT_END_DATE",
                    "customfieldvalue": f"{contract_end_date.month}/{contract_end_date.day}/{contract_end_date.year}",
                },
            ]
        },
        "potransitems": {"potransitem": deliverables},
    }
    try:
        connection = SageIntacctSDK(
            sender_id=settings.INTACCT_SENDER_ID,
            sender_password=settings.INTACCT_SENDER_PASSWORD,
            user_id=settings.INTACCT_USER_ID,
            company_id=settings.INTACCT_COMPANY_ID,
            user_password=settings.INTACCT_USER_PASSWORD,
        )
    except Exception as e:
        logging.error(e)
        return
    invoice = connection.invoice.post(data)
    return invoice


def fetch_project_details(external_projectid):
    """
    Fetch detail of a project contract from IntAcct.

    These details will be further used to fetch deliverables and create invoices.
    """
    formatted_filter = {"equalto": {"field": "DOCNO", "value": external_projectid}}

    try:
        connection = SageIntacctSDK(
            sender_id=settings.INTACCT_SENDER_ID,
            sender_password=settings.INTACCT_SENDER_PASSWORD,
            user_id=settings.INTACCT_USER_ID,
            company_id=settings.INTACCT_COMPANY_ID,
            user_password=settings.INTACCT_USER_PASSWORD,
        )
    except Exception as e:
        logging.error(e)
        return {}

    data = connection.project.get_by_query(filter_payload=formatted_filter)
    if data:
        return data[0]
    return {}
