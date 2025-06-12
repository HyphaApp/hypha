import django_tables2 as tables
from django.utils.html import format_html

from hypha.apply.projects.models import Project

from ..utils import get_project_title
from .models import Report


class ReportingTable(tables.Table):
    title = tables.LinkColumn(
        "funds:submissions:project", args=[tables.utils.A("submission_id")]
    )
    organization_name = tables.Column(
        accessor="submission__organization_name", verbose_name="Organization name"
    )
    current_report_status = tables.Column(
        attrs={"td": {"class": "status"}}, verbose_name="Status"
    )
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
            "title",
            "organization_name",
            "current_report_due_date",
            "current_report_status",
            "current_report_submitted_date",
            "current_report_last_notified_date",
        ]
        model = Project
        orderable = True
        attrs = {"class": "table overflow-x-auto reporting-table"}

    def render_title(self, record):
        return get_project_title(record)

    def render_current_report_status(self, value):
        return format_html("<span>{}</span>", value)


class ReportListTable(tables.Table):
    project = tables.LinkColumn(
        "funds:projects:reports:detail",
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
        attrs = {"class": "table border-x border-b mb-2 rounded-b-box projects-table"}

    def render_report_period(self, record):
        return f"{record.start} to {record.end_date}"

    def render_project(self, record):
        return get_project_title(record.project)
