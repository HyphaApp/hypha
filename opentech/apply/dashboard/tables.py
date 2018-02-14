from django.utils.text import mark_safe
import django_tables2 as tables
from django_tables2.utils import A

from opentech.apply.funds.models import ApplicationSubmission


class DashboardTable(tables.Table):
    title = tables.LinkColumn('funds:submission', args=[A('pk')], orderable=True)
    submit_time = tables.DateColumn(verbose_name="Submitted")
    page = tables.Column(verbose_name="Fund")
    status_name = tables.Column(verbose_name="Status", empty_values=[])

    class Meta:
        model = ApplicationSubmission
        fields = ('title', 'page', 'round', 'submit_time', 'user')
        template = "dashboard/tables/table.html"

    def render_user(self, value):
        return value.get_full_name()

    def render_status_name(self, value):
        return mark_safe(f'<span>{ value }</span>')
