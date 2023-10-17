import textwrap

import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import Invoice, Project, Report


class BaseInvoiceTable(tables.Table):
    invoice_number = tables.LinkColumn(
        "funds:projects:invoice-detail",
        verbose_name=_("Invoice Number"),
        args=[tables.utils.A("project__pk"), tables.utils.A("pk")],
    )
    project = tables.Column(verbose_name=_("Project Name"))
    status = tables.Column()
    requested_at = tables.DateColumn(verbose_name=_("Submitted"))

    def render_project(self, value):
        text = (textwrap.shorten(value.title, width=30, placeholder="..."),)
        return text[0]


class InvoiceDashboardTable(BaseInvoiceTable):
    class Meta:
        fields = [
            "requested_at",
            "invoice_number",
            "status",
            "project",
        ]
        model = Invoice
        order_by = ["-requested_at"]
        attrs = {"class": "invoices-table"}


class InvoiceListTable(BaseInvoiceTable):
    fund = tables.Column(verbose_name=_("Fund"), accessor="project__submission__page")
    lead = tables.Column(verbose_name=_("Lead"), accessor="project__lead")

    class Meta:
        fields = [
            "requested_at",
            "invoice_number",
            "status",
            "project",
            "lead",
            "fund",
        ]
        model = Invoice
        orderable = True
        order_by = ["-requested_at"]
        attrs = {"class": "invoices-table"}


class BaseProjectsTable(tables.Table):
    title = tables.LinkColumn(
        "funds:projects:detail",
        text=lambda r: textwrap.shorten(r.title, width=30, placeholder="..."),
        args=[tables.utils.A("pk")],
    )
    status = tables.Column(
        verbose_name=_("Status"), accessor="get_status_display", order_by=("status",)
    )
    fund = tables.Column(verbose_name=_("Fund"), accessor="submission__page")
    reporting = tables.Column(verbose_name=_("Reporting"), accessor="pk")
    last_payment_request = tables.DateColumn()
    end_date = tables.DateColumn(verbose_name=_("End Date"), accessor="proposed_end")

    def order_reporting(self, qs, is_descending):
        direction = "-" if is_descending else ""

        qs = qs.order_by(f"{direction}outstanding_reports")

        return qs, True

    def render_reporting(self, record):
        if not hasattr(record, "report_config"):
            return "-"

        if record.report_config.is_up_to_date():
            return "Up to date"

        if record.report_config.has_very_late_reports():
            display = (
                '<svg class="icon"><use xlink:href="#exclamation-point"></use></svg>'
            )
        else:
            display = ""

        display += f"{ record.report_config.outstanding_reports() } outstanding"
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
        orderable = False
        attrs = {"class": "projects-table"}


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
        attrs = {"class": "projects-table"}


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
        order_by = ("-end_date",)
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "projects-table"}

    def order_end_date(self, qs, desc):
        return qs.by_end_date(desc), True


class ReportListTable(tables.Table):
    project = tables.LinkColumn(
        "funds:projects:reports:detail",
        text=lambda r: textwrap.shorten(r.project.title, width=30, placeholder="..."),
        args=[tables.utils.A("pk")],
    )
    report_period = tables.Column(accessor="pk")
    submitted = tables.DateColumn()
    lead = tables.Column(accessor="project__lead")

    class Meta:
        fields = [
            "project",
            "submitted",
        ]
        sequence = ["project", "report_period", "..."]
        model = Report
        attrs = {"class": "responsive-table"}

    def render_report_period(self, record):
        return f"{record.start} to {record.end_date}"
