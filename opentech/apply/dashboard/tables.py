import django_tables2 as tables
from opentech.apply.funds.models import ApplicationSubmission


class DashboardTable(tables.Table):
    submit_time = tables.DateColumn(verbose_name="Submitted")
    status_name = tables.Column(verbose_name="Status")
    page = tables.Column(verbose_name="Fund")

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'status_name', 'page', 'round', 'submit_time', 'user')
        template = "dashboard/tables/table.html"

    def render_user(self, value):
        return value.get_full_name()
