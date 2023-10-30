from django.utils.translation import gettext as _

from hypha.apply.activity.adapters.utils import link_to

PROJECT_WAITING_PAF = "project_waiting_paf"
PROJECT_SUBMIT_PAF = "project_submit_paf"
PAF_REQUIRED_CHANGES = "paf_required_changes"
PAF_WAITING_ASSIGNEE = "paf_waiting_assignee"
PAF_WAITING_APPROVAL = "paf_waiting_approval"
PROJECT_WAITING_CONTRACT = "project_waiting_contract"
PROJECT_WAITING_CONTRACT_DOCUMENT = "project_waiting_contract_document"
PROJECT_WAITING_CONTRACT_REVIEW = "project_waiting_contract_review"
PROJECT_WAITING_INVOICE = "project_waiting_invoice"
INVOICE_REQUIRED_CHANGES = "invoice_required_changes"
INVOICE_WAITING_APPROVAL = "invoice_waiting_approval"
INVOICE_WAITING_PAID = "invoice_waiting_paid"
REPORT_DUE = "report_due"

TASKS_CODE_CHOICES = (
    (PROJECT_WAITING_PAF, "Project waiting PAF"),
    (PROJECT_SUBMIT_PAF, "Project submit PAF"),
    (PAF_REQUIRED_CHANGES, "PAF required changes"),
    (PAF_WAITING_ASSIGNEE, "PAF waiting assignee"),
    (PAF_WAITING_APPROVAL, "PAF waiting approval"),
    (PROJECT_WAITING_CONTRACT, "Project waiting contract"),
    (PROJECT_WAITING_CONTRACT_DOCUMENT, "Project waiting contract document"),
    (PROJECT_WAITING_CONTRACT_REVIEW, "Project waiting contract review"),
    (PROJECT_WAITING_INVOICE, "Project waiting invoice"),
    (INVOICE_REQUIRED_CHANGES, "Invoice required changes"),
    (INVOICE_WAITING_APPROVAL, "Invoice waiting approval"),
    (INVOICE_WAITING_PAID, "Invoice waiting paid"),
    (REPORT_DUE, "Report due"),
)


template_map = {
    # SUBMISSIONS ACTIONS
    # :todo: actions for mupltiple stages of submission
    # PROJECT actions
    # draft state (staff action)
    PROJECT_WAITING_PAF: {
        "text": _("Project <{link}|{related.title}> is waiting for PAF"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_SUBMIT_PAF: {
        "text": _("Project <{link}|{related.title}> is waiting for PAF submission"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    PAF_REQUIRED_CHANGES: {
        "text": _(
            "PAF for project <{link}|{related.title}> required changes or more information"
        ),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    # internal approval state (approvers/finance... action)
    PAF_WAITING_ASSIGNEE: {
        "text": _("PAF for project <{link}|{related.title}> is waiting for assignee"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    PAF_WAITING_APPROVAL: {
        "text": _(
            "PAF for project <{link}|{related.title}> is waiting for your approval"
        ),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    # contracting state (vendor/staff/contracting team action)
    PROJECT_WAITING_CONTRACT: {
        "text": _("Project <{link}|{related.title}> is waiting for contract"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_CONTRACT_DOCUMENT: {
        "text": _(
            "Project <{link}|{related.title}> is waiting for contracting documents"
        ),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_CONTRACT_REVIEW: {
        "text": _(
            "Contract for project <{link}|{related.title}> is waiting for review"
        ),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    # invoicing and reporting (vendor/staff/finance team action)
    PROJECT_WAITING_INVOICE: {
        "text": _("Project <{link}|{related.title}> is waiting for invoice"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_REQUIRED_CHANGES: {
        "text": _(
            "Invoice <{link}|{related.invoice_number}> required changes or more information"
        ),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_WAITING_APPROVAL: {
        "text": _(
            "Invoice <{link}|{related.invoice_number}> is waiting for your approval"
        ),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_WAITING_PAID: {
        "text": _("Invoice <{link}|{related.invoice_number}> is waiting to be paid"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
    REPORT_DUE: {
        "text": _("Report for project <{link}|{related.title}> is due"),
        "icon": "",
        "url": "{link}",
        "type": _("project"),
    },
}


def get_task_template(request, code, related_obj, **kwargs):
    try:
        template = template_map[code]
    except KeyError:
        # Unregistered code
        return
    template_kwargs = {
        "related": related_obj,
        "link": link_to(related_obj, request),
    }
    template["text"] = template["text"].format(**template_kwargs)
    template["url"] = template["url"].format(**template_kwargs)
    return template
