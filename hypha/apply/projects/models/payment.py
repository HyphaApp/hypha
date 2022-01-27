import decimal
import os

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q, Sum, Value
from django.db.models.fields import FloatField
from django.db.models.fields.related import ManyToManyField
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_fsm import FSMField, transition

from hypha.apply.utils.storage import PrivateStorage

SUBMITTED = 'submitted'
RESUBMITTED = 'resubmitted'
CHANGES_REQUESTED_BY_STAFF = 'changes_requested_staff'
CHANGES_REQUESTED_BY_FINANCE_1 = 'changes_requested_finance_1'
CHANGES_REQUESTED_BY_FINANCE_2 = 'changes_requested_finance_2'
APPROVED_BY_STAFF = 'approved_by_staff'
APPROVED_BY_FINANCE_1 = 'approved_by_finance_1'
APPROVED_BY_FINANCE_2 = 'approved_by_finance_2'
PAID = 'paid'
DECLINED = 'declined'

INVOICE_STATUS_CHOICES = [
    (SUBMITTED, _('Submitted')),
    (RESUBMITTED, _('Resubmitted')),
    (CHANGES_REQUESTED_BY_STAFF, _('Changes Requested by Staff')),
    (CHANGES_REQUESTED_BY_FINANCE_1, _('Changes Requested by Finance 1')),
    (CHANGES_REQUESTED_BY_FINANCE_2, _('Changes Requested by Finance 2')),
    (APPROVED_BY_STAFF, _('Approved by Staff')),
    (APPROVED_BY_FINANCE_1, _('Approved by Finance 1')),
    (APPROVED_BY_FINANCE_2, _('Approved by Finance 2')),
    (PAID, _('Paid')),
    (DECLINED, _('Declined')),
]

INVOICE_TRANISTION_TO_RESUBMITTED = [
    SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE_1, CHANGES_REQUESTED_BY_FINANCE_2,
]
INVOICE_STATUS_PM_CHOICES = [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED]
INVOICE_STATUS_FINANCE_1_CHOICES = [CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1, DECLINED]
INVOICE_STATUS_FINANCE_2_CHOICES = [CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2, PAID, DECLINED]


def invoice_status_user_choices(user):
    if user.is_finance_level2:
        return INVOICE_STATUS_FINANCE_2_CHOICES
    if user.is_finance:
        return INVOICE_STATUS_FINANCE_1_CHOICES
    if user.is_apply_staff:
        return INVOICE_STATUS_PM_CHOICES
    return []


def receipt_path(instance, filename):
    return f'projects/{instance.project_id}/payment_invoices/{filename}'


def invoice_path(instance, filename):
    return f'projects/{instance.project_id}/payment_invoices/{filename}'


class InvoiceQueryset(models.QuerySet):
    def in_progress(self):
        return self.exclude(status__in=[DECLINED, PAID])

    def rejected(self):
        return self.filter(status=DECLINED)

    def not_rejected(self):
        return self.exclude(status=DECLINED)

    def total_value(self, field):
        return self.aggregate(total=Coalesce(Sum(field), Value(0)))['total']

    def paid_value(self):
        return self.filter(status=PAID).total_value('paid_value')

    def unpaid_value(self):
        return self.filter(~Q(status=PAID)).total_value('paid_value')


class InvoiceDeliverable(models.Model):
    deliverable = models.ForeignKey(
        'Deliverable',
        on_delete=models.CASCADE,
        related_name='deliverables'
    )
    quantity = models.IntegerField(
        help_text=_('Quantity Selected on an Invoice'),
        default=0
    )

    def __str__(self):
        return self.deliverable.name

    def get_absolute_api_url(self):
        return reverse(
            'api:v1:remove-deliverables',
            kwargs={'pk': self.pk, 'invoice_pk': self.pk}
        )


class Invoice(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="invoices")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices")
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    amount = models.DecimalField(
        default=0,
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal('0.01'))],
    )
    paid_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal('0.01'))],
        null=True
    )
    document = models.FileField(upload_to=invoice_path, storage=PrivateStorage())
    requested_at = models.DateTimeField(auto_now_add=True)
    message_for_pm = models.TextField(blank=True, verbose_name=_('Message'))
    comment = models.TextField(blank=True)
    status = FSMField(default=SUBMITTED, choices=INVOICE_STATUS_CHOICES)
    deliverables = ManyToManyField(
        'InvoiceDeliverable',
        related_name='invoices'
    )
    objects = InvoiceQueryset.as_manager()

    def __str__(self):
        return _('Invoice requested for {project}').format(project=self.project)

    @transition(field=status, source=INVOICE_TRANISTION_TO_RESUBMITTED, target=RESUBMITTED)
    def transition_invoice_to_resubmitted(self):
        pass

    @property
    def has_changes_requested(self):
        return self.status == CHANGES_REQUESTED_BY_STAFF

    @property
    def status_display(self):
        return self.get_status_display()

    def can_user_delete(self, user):
        if user.is_applicant or user.is_apply_staff or user.is_finance or user.is_finance_level2 or user.is_contracting:
            if self.status in (SUBMITTED):
                return True

        return False

    def can_user_edit(self, user):
        if user.is_applicant:
            if self.status in {SUBMITTED, CHANGES_REQUESTED_BY_STAFF, RESUBMITTED}:
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE_1, CHANGES_REQUESTED_BY_FINANCE_2}:
                return True

        return False

    def can_user_change_status(self, user):
        if not (user.is_contracting or user.is_apply_staff or user.is_finance or user.is_finance_level2):
            return False  # Users can't change status

        if self.status in {PAID, DECLINED}:
            return False

        if user.is_contracting:
            if self.status in {SUBMITTED, CHANGES_REQUESTED_BY_STAFF, RESUBMITTED}:
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1}:
                return True

        if user.is_finance:
            if self.status in {APPROVED_BY_STAFF, CHANGES_REQUESTED_BY_FINANCE_1}:
                return True

        if user.is_finance_level2:
            if self.status in {CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_1}:
                return True

        return False

    @property
    def value(self):
        return self.paid_value or self.amount

    def get_absolute_url(self):
        return reverse(
            'apply:projects:invoice-detail',
            kwargs={'pk': self.project.pk, 'invoice_pk': self.pk}
        )

    @property
    def deliverables_total_amount(self):
        return self.deliverables.all().aggregate(total=Sum(F('deliverable__unit_price') * F('quantity'), output_field=FloatField()))

    @property
    def filename(self):
        return os.path.basename(self.document.name)


class SupportingDocument(models.Model):
    document = models.FileField(
        upload_to="supporting_documents", storage=PrivateStorage()
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='supporting_documents',
    )

    def __str__(self):
        return self.invoice.name + ' -> ' + self.document.name

    @property
    def filename(self):
        return os.path.basename(self.document.name)
