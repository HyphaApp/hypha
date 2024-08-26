import copy

from django.utils.translation import gettext as _

from hypha.apply.activity.adapters.utils import link_to

SUBMISSION_DRAFT = "submission_draft"
DETERMINATION_DRAFT = "determination_draft"
REVIEW_DRAFT = "review_draft"
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
COMMENT_TASK = "comment_task"

TASKS_CODE_CHOICES = (
    (COMMENT_TASK, "Comment Task"),
    (SUBMISSION_DRAFT, "Submission Draft"),
    (DETERMINATION_DRAFT, "Determination draft"),
    (REVIEW_DRAFT, "Review Draft"),
    (PROJECT_WAITING_PAF, "Project waiting project form"),
    (PROJECT_SUBMIT_PAF, "Project submit project form"),
    (PAF_REQUIRED_CHANGES, "Project form required changes"),
    (PAF_WAITING_ASSIGNEE, "Project form waiting assignee"),
    (PAF_WAITING_APPROVAL, "Project form waiting approval"),
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
    # ADD Manual Task
    COMMENT_TASK: {
        "text": _("{msg}"),
        "icon": "comment",
        "url": "{link}",
        "type": _("Comment"),
    },
    # SUBMISSIONS ACTIONS
    # :todo: actions for multiple stages of submission
    SUBMISSION_DRAFT: {
        "text": _(
            'A Submission draft [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting to be submitted'
        ),
        "icon": "comment",
        "url": "{link}",
        "type": _("Draft"),
    },
    DETERMINATION_DRAFT: {
        "text": _(
            'Determination draft for submission [<span class="truncate inline-block max-w-32 align-bottom ">{related.submission.title}</span>]({link} "{related.submission.title}") is waiting to be submitted',
        ),
        "icon": "edit-draft",
        "url": "{link}",
        "type": _("Draft"),
    },
    REVIEW_DRAFT: {
        "text": _(
            'Review draft for submission [<span class="truncate inline-block max-w-32 align-bottom ">{related.submission.title}</span>]({link} "{related.submission.title}") is waiting to be submitted'
        ),
        "icon": "edit-draft",
        "url": "{link}",
        "type": _("Draft"),
    },
    # PROJECT actions
    # draft state (staff action)
    PROJECT_WAITING_PAF: {
        "text": _(
            'Project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for project form'
        ),
        "icon": "dashboard-paf",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_SUBMIT_PAF: {
        "text": _(
            'Project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for project form submission'
        ),
        "icon": "dashboard-paf",
        "url": "{link}",
        "type": _("project"),
    },
    PAF_REQUIRED_CHANGES: {
        "text": _(
            'Project form for project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") required changes or more information'
        ),
        "icon": "dashboard-paf",
        "url": "{link}",
        "type": _("project"),
    },
    # internal approval state (approvers/finance... action)
    PAF_WAITING_ASSIGNEE: {
        "text": _(
            'Project form for project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for assignee'
        ),
        "icon": "dashboard-paf",
        "url": "{link}",
        "type": _("project"),
    },
    PAF_WAITING_APPROVAL: {
        "text": _(
            'Project form for project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for your approval'
        ),
        "icon": "dashboard-paf",
        "url": "{link}",
        "type": _("project"),
    },
    # contracting state (vendor/staff/contracting team action)
    PROJECT_WAITING_CONTRACT: {
        "text": _(
            'Project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for contract'
        ),
        "icon": "dashboard-contract",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_CONTRACT_DOCUMENT: {
        "text": _(
            'Project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for contracting documents'
        ),
        "icon": "dashboard-document",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_CONTRACT_REVIEW: {
        "text": _(
            'Contract for project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for review'
        ),
        "icon": "dashboard-contract",
        "url": "{link}",
        "type": _("project"),
    },
    # invoicing and reporting (vendor/staff/finance team action)
    PROJECT_WAITING_INVOICE: {
        "text": _(
            'Project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is waiting for invoice'
        ),
        "icon": "dashboard-invoice",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_REQUIRED_CHANGES: {
        "text": _(
            "Invoice [{related.invoice_number}]({link}) required changes or more information"
        ),
        "icon": "dashboard-invoice",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_WAITING_APPROVAL: {
        "text": _(
            "Invoice [{related.invoice_number}]({link}) is waiting for your approval"
        ),
        "icon": "dashboard-invoice",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_WAITING_PAID: {
        "text": _("Invoice [{related.invoice_number}]({link}) is waiting to be paid"),
        "icon": "dashboard-invoice",
        "url": "{link}",
        "type": _("project"),
    },
    REPORT_DUE: {
        "text": _(
            'Report for project [<span class="truncate inline-block max-w-32 align-bottom ">{related.title}</span>]({link} "{related.title}") is due'
        ),
        "icon": "dashboard-report",
        "url": "{link}",
        "type": _("project"),
    },
}


def get_task_template(request, task, **kwargs):
    related_obj = task.related_object
    code = task.code
    # if related_object is none/deleted and task remain there(edge case, avoiding 500)
    if not related_obj:
        return None

    templates = copy.deepcopy(template_map)
    try:
        template = templates[code]
    except KeyError:
        # Unregistered code
        return None
    template_kwargs = {
        "related": related_obj,
        "link": link_to(related_obj, request),
    }
    if task.code == COMMENT_TASK:
        template_kwargs["msg"] = related_obj.message
    template["text"] = template["text"].format(**template_kwargs)
    template["url"] = template["url"].format(**template_kwargs)
    # additional field
    template["id"] = task.id
    template["user"] = task.user
    return template
