import textwrap

import django_tables2 as tables

from .models import PaymentRequest, Project


class PaymentRequestsDashboardTable(tables.Table):
    project = tables.LinkColumn(
        'funds:projects:detail',
        text=lambda r: textwrap.shorten(r.project.title, width=30, placeholder="..."),
        args=[tables.utils.A('project_id')],
    )
    requested_value = tables.Column(verbose_name='Total Amount')
    date_from = tables.DateColumn(verbose_name='Start Date')
    date_to = tables.DateColumn(verbose_name='End Date')

    class Meta:
        fields = ['project', 'requested_value', 'date_from', 'date_to', 'status']
        model = PaymentRequest

    def render_requested_value(self, value):
        return f'${value}'


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
