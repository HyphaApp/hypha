import copy

from django.utils.translation import gettext as _

from hypha.apply.activity.adapters.utils import link_to

SUBMISSION_DRAFT = "submission_draft"
DETERMINATION_DRAFT = "determination_draft"
REVIEW_DRAFT = "review_draft"
PROJECT_WAITING_PF = "project_waiting_paf"
PROJECT_WAITING_SOW = "project_waiting_sow"
PROJECT_SUBMIT_PAF = "project_submit_pfs"
PROJECT_SUBMIT_SOW = "project_submit_sow"
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
DOWNLOAD_SUBMISSIONS_EXPORT = "download_submissions_export"
FAILED_SUBMISSIONS_EXPORT = "failed_submission_export"

TASKS_CODE_CHOICES = (
    (COMMENT_TASK, "Comment Task"),
    (SUBMISSION_DRAFT, "Submission Draft"),
    (DETERMINATION_DRAFT, "Determination draft"),
    (REVIEW_DRAFT, "Review Draft"),
    (PROJECT_WAITING_PF, "Project waiting project form"),
    (PROJECT_WAITING_SOW, "Project waiting scope of work"),
    (PROJECT_SUBMIT_PAF, "Project submit project form(s)"),
    (PROJECT_SUBMIT_SOW, "Project submit scope of work"),
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
    (DOWNLOAD_SUBMISSIONS_EXPORT, "Download exported submissions"),
    (FAILED_SUBMISSIONS_EXPORT, "Failed to generate submissions export file"),
)


template_map = {
    # ADD Manual Task
    # Use heroicons for "icon".
    COMMENT_TASK: {
        "text": _(
            '<span class="text-xs">{related.source.fund_name} #{related.source.application_id}</span><br>{related.user} assigned you a comment: <q class="text-fg-muted italic align-bottom">{msg}</q>'
        ),
        "icon": "chat-bubble-left-ellipsis",
        "url": "{link}",
        "type": _("Comment"),
    },
    # SUBMISSIONS ACTIONS
    # :todo: actions for multiple stages of submission
    SUBMISSION_DRAFT: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>A draft application <span class="truncate inline-block max-w-32 align-bottom ">"{related.title}"</span> is waiting to be submitted'
        ),
        "icon": "chat-bubble-left-ellipsis",
        "url": "{link}",
        "type": _("Draft"),
    },
    DETERMINATION_DRAFT: {
        "text": _(
            '<span class="text-xs">{related.submission.fund_name} #{related.submission.application_id}</span><br>Determination draft for submission <span class="truncate inline-block max-w-32 align-bottom">"{related.submission.title}"</span> is waiting to be submitted',
        ),
        "icon": "pencil-square",
        "url": "{link}",
        "type": _("Draft"),
    },
    REVIEW_DRAFT: {
        "text": _(
            '<span class="text-xs">{related.submission.fund_name} #{related.submission.application_id}</span><br>Review draft for submission <span class="truncate inline-block max-w-32 align-bottom">"{related.submission.title}"</span> is waiting to be submitted'
        ),
        "icon": "pencil-square",
        "url": "{link}",
        "type": _("Draft"),
    },
    # PROJECT ACTIONS
    # draft state (staff action)
    PROJECT_WAITING_PF: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project is waiting for project form'
        ),
        "icon": "clipboard-document-list",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_SOW: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project is waiting for scope of work'
        ),
        "icon": "clipboard-document-list",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_SUBMIT_PAF: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project is waiting for project form(s) submission'
        ),
        "icon": "clipboard-document-list",
        "url": "{link}",
        "type": _("project"),
    },
    PAF_REQUIRED_CHANGES: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project form requires changes or more information'
        ),
        "icon": "clipboard-document-list",
        "url": "{link}",
        "type": _("project"),
    },
    # internal approval state (approvers/finance... action)
    PAF_WAITING_ASSIGNEE: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project form is waiting for assignee'
        ),
        "icon": "clipboard-document-list",
        "url": "{link}",
        "type": _("project"),
    },
    PAF_WAITING_APPROVAL: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br> Project form is waiting for your approval'
        ),
        "icon": "clipboard-document-list",
        "url": "{link}",
        "type": _("project"),
    },
    # contracting state (vendor/staff/contracting team action)
    PROJECT_WAITING_CONTRACT: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project is waiting for contract'
        ),
        "icon": "document-duplicate",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_CONTRACT_DOCUMENT: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project is waiting for contracting documents'
        ),
        "icon": "arrow-down-on-square",
        "url": "{link}",
        "type": _("project"),
    },
    PROJECT_WAITING_CONTRACT_REVIEW: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Contract for project is waiting for review'
        ),
        "icon": "document-duplicate",
        "url": "{link}",
        "type": _("project"),
    },
    # invoicing and reporting (vendor/staff/finance team action)
    PROJECT_WAITING_INVOICE: {
        "text": _(
            '<span class="text-xs">{related.fund_name} #{related.application_id}</span><br>Project <span class="truncate inline-block max-w-32 align-bottom">"{related.title}"</span> is waiting for invoice'
        ),
        "icon": "document-currency-dollar",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_REQUIRED_CHANGES: {
        "text": _(
            "<span class='text-xs'>{related.project.fund_name} #{related.project.application_id}</span><br>Invoice no. {related.invoice_number} required changes or more information"
        ),
        "icon": "document-currency-dollar",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_WAITING_APPROVAL: {
        "text": _(
            "<span class='text-xs'>{related.project.fund_name} #{related.project.application_id}</span><br>Invoice no. {related.invoice_number} is waiting for your approval"
        ),
        "icon": "document-currency-dollar",
        "url": "{link}",
        "type": _("project"),
    },
    INVOICE_WAITING_PAID: {
        "text": _(
            "<span class='text-xs'>{related.project.fund_name} #{related.project.application_id}</span><br>Invoice no. {related.invoice_number} is waiting to be paid"
        ),
        "icon": "document-currency-dollar",
        "url": "{link}",
        "type": _("project"),
    },
    REPORT_DUE: {
        "text": _(
            '<span class="text-xs">{related.project.fund_name} #{related.project.application_id}</span><br>Report for project <span class="truncate inline-block max-w-32 align-bottom ">"{related.project.title}"</span> is due'
        ),
        "icon": "document-text",
        "url": "{link}",
        "type": _("project"),
    },
    # SUBMISSION EXPORT ACTIONS
    DOWNLOAD_SUBMISSIONS_EXPORT: {
        "text": _("Your generated submission export file is ready for download"),
        "icon": "arrow-down-tray",
        "url": "{link}",
        "type": _("export"),
    },
    FAILED_SUBMISSIONS_EXPORT: {
        "text": _(
            "There was an issue generating your submission export file, please try again."
        ),
        "icon": "exclamation-circle",
        "url": "{link}",
        "type": _("export"),
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
        # Replace all newlines with spaces and truncate to 60 characters
        message = " ".join(related_obj.message.splitlines())
        if len(message) > 60:
            template_kwargs["msg"] = message[:57] + "…"
        else:
            template_kwargs["msg"] = message
    template["text"] = template["text"].format(**template_kwargs)
    template["url"] = template["url"].format(**template_kwargs)

    # additional field
    template["id"] = task.id
    template["user"] = task.user
    template["created_at"] = task.created_at
    return template
