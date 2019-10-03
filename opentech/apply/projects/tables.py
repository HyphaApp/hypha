import textwrap

import django_tables2 as tables
from django.db.models import F, Sum
from django.contrib.humanize.templatetags.humanize import intcomma

from .models import PaymentRequest, Project


class BasePaymentRequestsTable(tables.Table):
    project = tables.LinkColumn(
        'funds:projects:payments:detail',
        text=lambda r: textwrap.shorten(r.project.title, width=30, placeholder="..."),
        args=[tables.utils.A('pk')],
    )
    status = tables.Column()
    requested_at = tables.DateColumn(verbose_name='Submitted')

    def render_value(self, value):
        return f'${value}'


class PaymentRequestsDashboardTable(BasePaymentRequestsTable):
    date_from = tables.DateColumn(verbose_name='Period Start')
    date_to = tables.DateColumn(verbose_name='Period End')

    class Meta:
        fields = [
            'project',
            'status',
            'requested_at',
            'date_from',
            'date_to',
            'value',
        ]
        model = PaymentRequest
        orderable = False
        order_by = ['-requested_at']


class PaymentRequestsListTable(BasePaymentRequestsTable):
    fund = tables.Column(verbose_name="Fund", accessor='project.submission.page')
    lead = tables.Column(verbose_name="Lead", accessor='project.lead')

    class Meta:
        fields = [
            'project',
            'fund',
            'lead',
            'status',
            'requested_at',
            'value',
        ]
        model = PaymentRequest
        orderable = True
        order_by = ['-requested_at']

    def order_value(self, qs, is_descending):
        direction = '-' if is_descending else ''

        qs = qs.order_by(f'{direction}paid_value', f'{direction}requested_value')

        return qs, True


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
        return f'${intcomma(record.amount_paid)} / ${intcomma(record.value)}'


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
        ).order_by(f'{direction}paid_ratio', f'{direction}value')

        return qs, True

    def order_end_date(self, qs, desc):
        return qs.by_end_date(desc), True
