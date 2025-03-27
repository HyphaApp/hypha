import textwrap

import django_tables2 as tables
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from hypha.apply.projects.models import Project

from .models import Report


class ReportingTable(tables.Table):
    pk = tables.Column(
        verbose_name=_("Project #"),
    )
    submission_id = tables.Column(
        verbose_name=_("Submission #"),
    )
    title = tables.LinkColumn("funds:projects:detail", args=[tables.utils.A("pk")])
    organization_name = tables.Column(
        accessor="submission__organization_name", verbose_name="Organization name"
    )
    current_report_status = tables.Column(
        attrs={"td": {"class": "status"}}, verbose_name="Status"
    )

    def render_current_report_status(self, value):
        return format_html("<span>{}</span>", value)

    current_report_submitted_date = tables.Column(
        verbose_name="Submitted date", accessor="current_report_submitted_date__date"
    )
    current_report_due_date = tables.Column(
        verbose_name="Due Date", accessor="report_config__current_report__end_date"
    )
    current_report_last_notified_date = tables.Column(
        verbose_name="Last Notified",
        accessor="report_config__current_report__notified__date",
    )

    class Meta:
        fields = [
            "pk",
            "title",
            "submission_id",
            "organization_name",
            "current_report_due_date",
            "current_report_status",
            "current_report_submitted_date",
            "current_report_last_notified_date",
        ]
        model = Project
        orderable = True
        attrs = {"class": "reporting-table"}


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
        template_name = "application_projects/tables/table.html"
        attrs = {"class": "projects-table"}

    def render_report_period(self, record):
        return f"{record.start} to {record.end_date}"
