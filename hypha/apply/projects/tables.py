import json

import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_tables2.utils import A
from heroicons.templatetags.heroicons import heroicon_outline

from hypha.apply.funds.tables import LabeledCheckboxColumn

from .forms.payment import get_invoice_possible_transition_for_user
from .models import Invoice, PAFApprovals, Project
from .utils import get_project_title


def render_invoice_actions(table, record):
    user = table.context["user"]
    actions = get_invoice_possible_transition_for_user(user, invoice=record)
    return json.dumps([str(slugify(action)) for action, _ in actions])


class BaseInvoiceTable(tables.Table):
    invoice_number = tables.LinkColumn(
        "funds:projects:invoice-detail",
        verbose_name=_("Invoice Number"),
        args=[tables.utils.A("project__submission__pk"), tables.utils.A("pk")],
        attrs={
            "td": {
                "class": "js-title",  # using title as class because of batch-actions.js
            },
            "a": {
                "class": "truncate inline-block w-[calc(100%-2rem)] after:content-[''] after:block",
            },
        },
    )
    status = tables.Column(
        attrs={"td": {"data-actions": render_invoice_actions, "class": "js-actions"}},
    )
    requested_at = tables.DateColumn(verbose_name=_("Submitted"))
    invoice_date = tables.DateColumn(verbose_name=_("Invoice date"))


class InvoiceDashboardTable(BaseInvoiceTable):
    project = tables.Column(verbose_name=_("Project Name"))

    class Meta:
        fields = [
            "requested_at",
            "invoice_number",
            "status",
            "project",
        ]
        model = Invoice
        order_by = ["-requested_at"]
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table overflow-x-auto invoices-table"}

    def render_project(self, record):
        return get_project_title(record.project)


class FinanceInvoiceTable(BaseInvoiceTable):
    vendor_name = tables.Column(verbose_name=_("Vendor Name"), empty_values=())
    selected = LabeledCheckboxColumn(
        accessor=A("pk"),
        attrs={
            "input": {"class": "js-batch-select"},
            "th__input": {"class": "js-batch-select-all"},
        },
    )

    class Meta:
        fields = [
            "selected",
            "invoice_date",
            "requested_at",
            "vendor_name",
            "invoice_number",
            "invoice_amount",
            "status",
        ]
        model = Invoice
        orderable = True
        sequence = fields
        order_by = ["-requested_at", "invoice_date"]
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table overflow-x-auto invoices-table"}
        row_attrs = {
            "data-record-id": lambda record: record.id,
        }

    def render_vendor_name(self, record):
        return record.project.user


class AdminInvoiceListTable(BaseInvoiceTable):
    project = tables.Column(verbose_name=_("Project Name"))
    selected = LabeledCheckboxColumn(
        accessor=A("pk"),
        attrs={
            "th": {
                "class": "w-8",
            },
            "input": {"class": "js-batch-select"},
            "th__input": {"class": "js-batch-select-all"},
        },
    )

    class Meta:
        fields = [
            "selected",
            "invoice_number",
            "invoice_date",
            "requested_at",
            "status",
            "project",
        ]
        model = Invoice
        orderable = True
        sequence = fields
        order_by = ["-requested_at"]
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table overflow-x-auto invoices-table"}
        row_attrs = {
            "data-record-id": lambda record: record.id,
        }

    def render_project(self, record):
        return get_project_title(record.project)


class BaseProjectsTable(tables.Table):
    title = tables.LinkColumn(
        "funds:submissions:project",
        args=[tables.utils.A("application_id")],
    )
    status = tables.Column(
        verbose_name=_("Status"), accessor="get_status_display", order_by=("status",)
    )
    fund = tables.Column(verbose_name=_("Fund"), accessor="submission__page")
    reporting = tables.Column(verbose_name=_("Reporting"), accessor="pk")
    last_payment_request = tables.DateColumn()
    end_date = tables.DateColumn(verbose_name=_("End date"), accessor="proposed_end")

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
            return "Up to date"

        if record.report_config.has_very_late_reports():
            display = f"<span class='text-red-500 inline-block align-text-bottom me-1'>{heroicon_outline(name='exclamation-triangle', size=20)}</span>"
        else:
            display = ""

        display += f"{record.report_config.outstanding_reports()} outstanding"
        return mark_safe(display)


class ProjectsDashboardTable(BaseProjectsTable):
    class Meta:
        fields = [
            "title",
            "status",
            "fund",
            "reporting",
            "last_payment_request",
            "end_date",
        ]
        model = Project
        template_name = "application_projects/tables/table.html"
        orderable = False
        attrs = {"class": "table overflow-x-auto projects-table"}


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
        attrs = {"class": "table overflow-x-auto projects-table"}


class PAFForReviewDashboardTable(tables.Table):
    date_requested = tables.DateColumn(
        verbose_name=_("Date requested"),
        accessor="created_at",
        orderable=True,
    )
    title = tables.LinkColumn(
        "funds:submissions:project",
        args=[tables.utils.A("application_id")],
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
            "fund",
            "reporting",
            "last_payment_request",
            "end_date",
        ]
        model = Project
        orderable = True
        order_by = ("end_date",)
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "table overflow-x-auto projects-table"}
