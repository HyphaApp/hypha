from django.conf import settings

from .sageintacctsdk import SageIntacctSDK


def fetch_deliverables(program_project_id=''):
    if not program_project_id:
        return []
    formatted_filter = {
        'and': {
            'equalto': [
                {'field': 'DOCPARID', 'value': 'Project Contract'},
                {'field': 'DEPARTMENTID', 'value': program_project_id}
            ],
            'greaterthan': {'field': 'QTY_REMAINING', 'value': 0.0}
        }
    }

    connection = SageIntacctSDK(
        sender_id=settings.INTACCT_SENDER_ID,
        sender_password=settings.INTACCT_SENDER_PASSWORD,
        user_id=settings.INTACCT_USER_ID,
        company_id=settings.INTACCT_COMPANY_ID,
        user_password=settings.INTACCT_USER_PASSWORD
    )

    deliverables = connection.purchasing.get_by_query(filter_payload=formatted_filter)

    return deliverables
