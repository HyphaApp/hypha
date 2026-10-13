import json

import django_tables2 as tables
from django.conf import settings
from django.db.models import F
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django_tables2.utils import A
from heroicons.templatetags.heroicons import heroicon_outline

from hypha.apply.funds.tables import LabeledCheckboxColumn
from hypha.core.tables import RelativeTimeColumn

from .forms.invoice import get_invoice_possible_transition_for_user
from .models import Disbursement, Invoice, PAFApprovals, Project
from .payments import PaymentsFlow
from .utils import (
    format_local_minute,
    format_trimmed_amount,
    get_contract_approved_amounts_cell,
    get_project_title,
)


def render_invoice_actions(table, record):
    user = table.context["user"]
    actions = get_invoice_possible_transition_for_user(user, invoice=record)
    return json.dumps([str(slugify(action)) for action, _ in actions])


class BaseInvoiceTable(tables.Table):
    invoice_number = tables.Column(
        verbose_name=_("Invoice #"),
        linkify=True,
        attrs={
            "a": {
                "class": "link link-hover text-h4 font-semibold break-words line-clamp-2 max-w-md",
            },
        },
    )
    status = tables.Column(
        attrs={"td": {"data-actions": render_invoice_actions, "class": "js-actions"}},
    )
    requested_at = tables.DateColumn(verbose_name=_("Submitted"))
    invoice_date = tables.DateColumn(verbose_name=_("Invoice date"))
    project = tables.Column(
        verbose_name=_("Project Title"), attrs={"td": {"class": "max-w-md"}}
    )

    class Meta:
        row_attrs = {
            "onclick": lambda record: (
                f"window.location.href='{record.get_absolute_url()}'"
            ),
            "class": "table-row-link",
            "role": "button",
            "tabindex": "0",  # Accessibility
        }

    def render_tags(self, record):
        tags = record.tags.all()
        if not tags:
            return mark_safe("<span class='text-base-content/40'>—</span>")
        badges = "".join(
            format_html(
                "<span class='badge badge-soft badge-neutral whitespace-nowrap'>{}</span>",
                tag.name,
            )
            for tag in tags
        )
        return mark_safe(f"<div class='flex flex-wrap gap-1'>{badges}</div>")

    def render_requested_at(self, record):
        return format_html(
            "<relative-time datetime='{}' prefix=''>{}</relative-time>",
            record.requested_at.isoformat(),
            record.requested_at.strftime(settings.SHORT_DATETIME_FORMAT),
        )

    def render_status(self, record):
        status = record.status
        status_display = record.get_status_display()

        badge_class = {
            "changes_requested_staff": "badge-warning",
            "payment_failed": "badge-error",
            "paid": "badge-success",
            "declined": "badge-error",
        }

        return format_html(
            "<span class='badge badge-soft whitespace-nowrap {}' data-status='{}'>{}</span>",
            badge_class.get(status, "badge-info"),
            status,
            status_display,
        )


class InvoiceDashboardTable(BaseInvoiceTable):
    class Meta(BaseInvoiceTable.Meta):
        fields = [
            "invoice_number",
            "requested_at",
            "status",
            "project",
        ]
        model = Invoice
        order_by = ["-requested_at"]
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table invoices-table invoivceDashboardTable"}
        orderable = False

    def render_project(self, record):
        return get_project_title(record.project)


class FinanceInvoiceTable(BaseInvoiceTable):
    vendor_name = tables.Column(verbose_name=_("Vendor Name"), empty_values=())
    tags = tables.Column(verbose_name=_("Tags"), orderable=False, empty_values=())
    selected = LabeledCheckboxColumn(
        accessor=A("pk"),
        attrs={
            "input": {"class": "js-batch-select checkbox"},
            "th__input": {"class": "js-batch-select-all checkbox"},
        },
    )

    class Meta(BaseInvoiceTable.Meta):
        fields = [
            "selected",
            "invoice_number",
            "invoice_date",
            "vendor_name",
            "status",
            "requested_at",
            "invoice_amount",
            "tags",
        ]
        model = Invoice
        orderable = True
        sequence = fields
        order_by = ["-requested_at", "invoice_date"]
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table border-x border-b mb-2 invoices-table"}
        row_attrs = {
            **BaseInvoiceTable.Meta.row_attrs,
            "data-record-id": lambda record: record.id,
        }

    def render_vendor_name(self, record):
        return record.project.user


class AdminInvoiceListTable(BaseInvoiceTable):
    project = tables.Column(verbose_name=_("Project Name"))
    tags = tables.Column(verbose_name=_("Tags"), orderable=False, empty_values=())
    selected = LabeledCheckboxColumn(
        accessor=A("pk"),
        attrs={
            "th": {
                "class": "w-8",
            },
            "input": {"class": "js-batch-select checkbox"},
            "th__input": {"class": "js-batch-select-all checkbox"},
        },
    )

    class Meta(BaseInvoiceTable.Meta):
        fields = [
            "selected",
            "invoice_number",
            "invoice_date",
            "status",
            "requested_at",
            "project",
            "tags",
        ]
        model = Invoice
        orderable = True
        sequence = fields
        order_by = ["-requested_at"]
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table border-x border-b mb-2 invoices-table"}
        row_attrs = {
            **BaseInvoiceTable.Meta.row_attrs,
            "data-record-id": lambda record: record.id,
        }

    def render_project(self, record):
        return get_project_title(record.project)


class BaseProjectsTable(tables.Table):
    title = tables.LinkColumn(
        "funds:submissions:project",
        args=[tables.utils.A("submission_id"), tables.utils.A("pk")],
        attrs={
            "a": {
                "class": "link link-hover text-h4 font-semibold break-words line-clamp-2 max-w-md"
            }
        },
    )
    status = tables.Column(
        verbose_name=_("Status"), accessor="get_status_display", order_by=("status",)
    )
    contractor = tables.Column(verbose_name=_("Contractor"), accessor="user")
    fund = tables.Column(verbose_name=_("Fund"), accessor="submission__page")
    contract_number = tables.Column(verbose_name=_("Contract #"), default="-")
    reporting = tables.Column(verbose_name=_("Reporting"), accessor="pk")
    last_payment_request = RelativeTimeColumn()
    # render_contract_approved_total reads annotations that
    # Project.objects.for_table() provides.
    contract_approved_total = tables.Column(
        verbose_name=_("Contracts total"),
        accessor="pk",
        order_by="contract_approved_total",
        attrs={"th": {"align": "right"}, "td": {"align": "right"}},
    )
    end_date = RelativeTimeColumn(verbose_name=_("End date"), accessor="proposed_end")

    def __init__(self, *args, **kwargs):
        if settings.PROJECTS_PAYMENTS_FLOW != PaymentsFlow.DISBURSEMENTS:
            exclude = list(kwargs.get("exclude") or [])
            exclude.append("contract_approved_total")
            kwargs["exclude"] = exclude
        super().__init__(*args, **kwargs)

    def order_reporting(self, qs, is_descending):
        direction = "-" if is_descending else ""

        qs = qs.order_by(f"{direction}outstanding_reports")

        return qs, True

    def render_title(self, record):
        return get_project_title(record)

    def render_reporting(self, record):
        if not hasattr(record, "report_config"):
            return "-"

        if record.report_config.is_up_to_date():
            return _("Up to date")

        if record.report_config.has_very_late_reports():
            display = f"<span class='text-red-500 inline-block align-text-bottom me-1'>{heroicon_outline(name='exclamation-triangle', size=20)}</span>"
        else:
            display = ""

        outstanding_count = record.report_config.outstanding_reports()
        display += gettext("{count} outstanding").format(count=outstanding_count)
        return mark_safe(display)

    def render_contract_approved_total(self, record):
        return get_contract_approved_amounts_cell(record, format_trimmed_amount)

    def order_organization_name(self, qs, is_descending):
        f = F("submission__form_data__organization_name")

        qs = (
            qs.order_by(f.desc(nulls_last=True))
            if is_descending
            else qs.order_by(f.asc(nulls_last=True))
        )

        return qs, True

    def render_organization_name(self, record):
        return record.submission.form_data.get("organization_name", "")


class ProjectsDashboardTable(BaseProjectsTable):
    class Meta:
        fields = [
            "title",
            "status",
            "fund",
            "reporting",
            "last_payment_request",
            "contract_approved_total",
            "end_date",
        ]
        model = Project
        template_name = "application_projects/tables/table.html"
        orderable = False
        attrs = {"class": "table projects-table"}


class ProjectsAssigneeDashboardTable(BaseProjectsTable):
    class Meta:
        fields = [
            "title",
            "fund",
            "lead",
            "reporting",
            "last_payment_request",
            "end_date",
        ]
        model = Project
        orderable = False
        exclude = ["status"]
        attrs = {"class": "table projects-table"}


class PAFForReviewDashboardTable(tables.Table):
    date_requested = tables.DateColumn(
        verbose_name=_("Date requested"),
        accessor="created_at",
        orderable=True,
    )
    title = tables.LinkColumn(
        "funds:submissions:project",
        args=[
            tables.utils.A("project__submission_id"),
            tables.utils.A("project__pk"),
        ],
        orderable=False,
    )
    status = tables.Column(verbose_name=_("Status"), accessor="pk", orderable=False)
    fund = tables.Column(
        verbose_name=_("Fund"), accessor="project__submission__page", orderable=False
    )

    assignee = tables.Column(
        verbose_name=_("Assignee"), accessor="user", orderable=False
    )

    class Meta:
        fields = ["date_requested", "title", "fund", "status", "assignee"]
        model = PAFApprovals
        template_name = (
            "funds/tables/table.html"  # todo: update it with Project table template
        )
        attrs = {"class": "table paf-review-table"}

    def order_date_requested(self, qs, is_descending):
        direction = "-" if is_descending else ""

        qs = qs.order_by(f"{direction}created_at")

        return qs, True

    def render_status(self, record):
        if record.user:
            return _("Waiting for approval")
        else:
            return _("Waiting for assignee")

    def render_title(self, record):
        return get_project_title(record.project)


class ProjectsListTable(BaseProjectsTable):
    class Meta:
        fields = [
            "title",
            "status",
            "lead",
            "contractor",
            "fund",
            "contract_number",
            "reporting",
            "last_payment_request",
            "contract_approved_total",
            "end_date",
        ]
        model = Project
        orderable = True
        order_by = ("end_date",)
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table projects-table"}


class AdminDisbursementListTable(tables.Table):
    """Every disbursement across all projects, one row per disbursement.

    The contract's requested/approved amounts repeat on each of its rows.
    Amount columns carry no unit: currency is its own column so filtering to
    a single currency guarantees a numeric total. The disbursement date
    renders as ISO 8601; the entry date renders compactly in the active
    timezone, rounded to the nearest minute (strict RFC 3339 stays in the
    CSV export). The entry date carries a tooltip showing the edited time
    when an edit rounds to a different minute, marked with an asterisk.

    """

    date = tables.Column(verbose_name=_("Disbursement date"))
    created_at = tables.Column(verbose_name=_("Date recorded"))
    project = tables.LinkColumn(
        "funds:submissions:project",
        text=lambda record: get_project_title(record.contract.project),
        args=[A("contract__project__submission_id"), A("contract__project__pk")],
        order_by=("contract__project__title",),
        attrs={
            "a": {
                "class": "link link-hover text-h4 font-semibold break-words line-clamp-2 max-w-md",
            },
        },
    )
    contract = tables.LinkColumn(
        "apply:projects:contract",
        text=lambda record: f"#{record.contract_id}",
        args=[A("contract__project__id"), A("contract_id")],
        order_by=("contract_id",),
    )
    contract_requested = tables.Column(
        verbose_name=_("Contract requested"),
        accessor=A("contract__amount_requested"),
        attrs={"th": {"class": "text-right"}, "td": {"class": "text-right"}},
    )
    contract_approved = tables.Column(
        verbose_name=_("Contract approved"),
        accessor=A("contract__amount_approved"),
        attrs={"th": {"class": "text-right"}, "td": {"class": "text-right"}},
    )
    currency = tables.Column(
        verbose_name=_("Currency"),
        accessor=A("contract__currency"),
        default="—",
    )
    amount = tables.Column(
        verbose_name=_("Amount disbursed"),
        attrs={"th": {"class": "text-right"}, "td": {"class": "text-right"}},
    )
    notes = tables.Column(attrs={"td": {"class": "max-w-md"}})

    class Meta:
        fields = [
            "project",
            "date",
            "created_at",
            "contract",
            "contract_requested",
            "contract_approved",
            "currency",
            "amount",
            "notes",
        ]
        model = Disbursement
        orderable = True
        order_by = ("-date", "-created_at")
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table disbursements-table"}

    def render_date(self, record):
        return record.date.isoformat()

    def render_created_at(self, record):
        entry = format_local_minute(record.created_at)
        edited = format_local_minute(record.updated_at)
        if entry == edited:
            return entry
        return format_html(
            '<span title="{}">{}*</span>',
            _("Edited {}").format(edited),
            entry,
        )

    def render_contract_requested(self, record):
        return format_trimmed_amount(record.contract.amount_requested)

    def render_contract_approved(self, record):
        return format_trimmed_amount(record.contract.amount_approved)

    def render_amount(self, record):
        return format_trimmed_amount(record.amount)
