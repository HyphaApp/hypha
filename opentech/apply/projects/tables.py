import textwrap

import django_tables2 as tables
from django.db.models import F, Sum
from django.utils.safestring import mark_safe

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
        orderable = False

    def render_requested_value(self, value):
        return f'${value}'


class PaymentRequestsListTable(tables.Table):
    requested_value = tables.Column(verbose_name='Amount Requested', orderable=True)
    status = tables.Column()
    date_to = tables.DateColumn(verbose_name='End Date', orderable=True)
    fund = tables.Column(verbose_name='Fund', accessor='project.submission.page')

    class Meta:
        fields = ['project', 'requested_value', 'status', 'date_to', 'fund']
        model = PaymentRequest
        orderable = False

    def render_project(self, value):
        text = textwrap.shorten(value.title, width=30, placeholder="...")
        url = f'{value.get_absolute_url()}#payment-requests'

        return mark_safe(f'<a href="{url}">{text}</a>')

    def render_requested_value(self, value):
        return f'${value}'


class BaseProjectsTable(tables.Table):
    title = tables.LinkColumn(
        'funds:projects:detail',
        text=lambda r: textwrap.shorten(r.title, width=30, placeholder="..."),
        args=[tables.utils.A('pk')],
    )
    status = tables.Column(verbose_name='Status', accessor='get_status_display', order_by=('status',))
    fund = tables.Column(verbose_name='Fund', accessor='submission.page')
    last_payment_request = tables.DateColumn()
    end_date = tables.DateColumn(verbose_name='End Date', accessor='proposed_end')
    fund_allocation = tables.Column(verbose_name='Fund Allocation', accessor='value')

    def render_fund_allocation(self, record):
        return f'${record.amount_paid} / ${record.value}'


class ProjectsDashboardTable(BaseProjectsTable):
    class Meta:
        fields = [
            'title',
            'status',
            'fund',
            'last_payment_request',
            'end_date',
            'fund_allocation',
        ]
        model = Project
        orderable = False


class ProjectsListTable(BaseProjectsTable):
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
        orderable = True
        order_by = ('-end_date',)

    def order_fund_allocation(self, qs, is_descending):
        direction = '-' if is_descending else ''

        qs = qs.annotate(
            paid_ratio=Sum('payment_requests__paid_value') / F('value'),
        ).order_by(f'{direction}paid_ratio', 'value')

        return qs, True

    def order_end_date(self, qs, desc):
        return qs.by_end_date(desc), True
