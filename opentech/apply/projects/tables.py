import textwrap

import django_tables2 as tables

from .models import Project


class ProjectsDashboardTable(tables.Table):
    title = tables.LinkColumn(
        'funds:projects:detail',
        text=lambda r: textwrap.shorten(r.title, width=30, placeholder="..."),
        args=[tables.utils.A('pk')],
    )
    status = tables.Column(verbose_name='Status', accessor='status')
    fund = tables.Column(verbose_name='Fund', accessor='submission.page')
    end_date = tables.DateColumn(verbose_name='End Date', accessor='proposed_end')
    fund_allocation = tables.Column(verbose_name='Fund Allocation', accessor='value')

    class Meta:
        fields = ['title', 'status', 'fund', 'end_date', 'fund_allocation']
        model = Project
        # orderable = False

    def render_fund_allocation(self, value):
        return f'${value}'
