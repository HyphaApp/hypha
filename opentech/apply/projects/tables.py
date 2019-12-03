import textwrap

import django_tables2 as tables
from django.db.models import F, Sum
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe

from .models import PaymentRequest, Project, Report


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
    reporting = tables.Column(verbose_name='Reporting', accessor='pk')
    last_payment_request = tables.DateColumn()
    end_date = tables.DateColumn(verbose_name='End Date', accessor='proposed_end')
    fund_allocation = tables.Column(verbose_name='Fund Allocation', accessor='value')

    def order_reporting(self, qs, is_descending):
        direction = '-' if is_descending else ''

        qs = qs.order_by(f'{direction}outstanding_reports')

        return qs, True

    def render_fund_allocation(self, record):
        return f'${intcomma(record.amount_paid)} / ${intcomma(record.value)}'

    def render_reporting(self, record):
        if not hasattr(record, 'report_config'):
            return '-'

        if record.report_config.is_up_to_date():
            return 'Up to date'

        if record.report_config.has_very_late_reports():
            display = '<svg class="icon"><use xlink:href="#exclamation-point"></use></svg>'
        else:
            display = ''

        display += f'{ record.report_config.outstanding_reports() } outstanding'
        return mark_safe(display)


class ProjectsDashboardTable(BaseProjectsTable):
    class Meta:
        fields = [
            'title',
            'status',
            'fund',
            'reporting',
            'last_payment_request',
            'end_date',
            'fund_allocation',
        ]
        model = Project
        orderable = False
        attrs = {'class': 'projects-table'}


class ProjectsListTable(BaseProjectsTable):
    class Meta:
        fields = [
            'title',
            'status',
            'lead',
            'fund',
            'reporting',
            'last_payment_request',
            'end_date',
            'fund_allocation',
        ]
        model = Project
        orderable = True
        order_by = ('-end_date',)
        attrs = {'class': 'projects-table'}

    def order_fund_allocation(self, qs, is_descending):
        direction = '-' if is_descending else ''

        qs = qs.annotate(
            paid_ratio=Sum('payment_requests__paid_value') / F('value'),
        ).order_by(f'{direction}paid_ratio', f'{direction}value')

        return qs, True

    def order_end_date(self, qs, desc):
        return qs.by_end_date(desc), True


class ReportListTable(tables.Table):
    project = tables.LinkColumn(
        'funds:projects:reports:detail',
        text=lambda r: textwrap.shorten(r.project.title, width=30, placeholder="..."),
        args=[tables.utils.A('pk')],
    )
    report_period = tables.Column(accessor='pk')
    submitted = tables.DateColumn()
    lead = tables.Column(accessor='project.lead')

    class Meta:
        fields = [
            'project',
            'submitted',
        ]
        sequence = [
            'project',
            'report_period',
            '...'
        ]
        model = Report
        attrs = {'class': 'responsive-table'}

    def render_report_period(self, record):
        return f"{record.start} to {record.end_date}"
