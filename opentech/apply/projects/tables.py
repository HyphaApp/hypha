import textwrap

import django_tables2 as tables
from django.db.models import F, Sum

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


class ProjectsListTable(tables.Table):
    title = tables.LinkColumn(
        'funds:projects:detail',
        text=lambda r: textwrap.shorten(r.title, width=30, placeholder="..."),
        args=[tables.utils.A('pk')],
    )
    status = tables.Column()
    fund = tables.Column(verbose_name='Fund', accessor='submission.page')
    last_payment_request = tables.DateColumn()
    end_date = tables.DateColumn(verbose_name='End Date', accessor='proposed_end')
    fund_allocation = tables.Column(verbose_name='Fund Allocation', accessor='value')

    class Meta:
        fields = [
            'title',
            'status',
            'lead',
            'fund',
            'last_payment_request',
            'end_date',
            'fund_allocation',
        ]
        model = Project

    def order_fund_allocation(self, qs, is_descending):
        direction = '-' if is_descending else ''

        qs = (qs.annotate(percentage_paid=Sum('payment_requests__paid_value') / F('value') * 100)
                .order_by(f'{direction}percentage_paid'))

        return qs, True

    def render_fund_allocation(self, record):
        amount_paid = record.amount_paid or 0
        return f'${amount_paid} / ${record.value}'
