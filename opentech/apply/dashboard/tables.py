import django_tables2 as tables
from opentech.apply.funds.models import ApplicationSubmission


class DashboardTable(tables.Table):
    submit_time = tables.DateColumn(verbose_name="Submitted")
    page = tables.Column(verbose_name="Fund")

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'page', 'submit_time')
        template = "dashboard/tables/table.html"
