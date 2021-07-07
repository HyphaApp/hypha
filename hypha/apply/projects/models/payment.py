import decimal
import os

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse

from hypha.apply.utils.storage import PrivateStorage

SUBMITTED = 'submitted'
CHANGES_REQUESTED = 'changes_requested'
UNDER_REVIEW = 'under_review'
PAID = 'paid'
DECLINED = 'declined'
REQUEST_STATUS_CHOICES = [
    (SUBMITTED, 'Submitted'),
    (CHANGES_REQUESTED, 'Changes Requested'),
    (UNDER_REVIEW, 'Under Review'),
    (PAID, 'Paid'),
    (DECLINED, 'Declined'),
]


def receipt_path(instance, filename):
    return f'projects/{instance.payment_request.project_id}/payment_receipts/{filename}'


def invoice_path(instance, filename):
    return f'projects/{instance.project_id}/payment_invoices/{filename}'


class PaymentApproval(models.Model):
    request = models.ForeignKey('PaymentRequest', on_delete=models.CASCADE, related_name="approvals")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_approvals")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Approval for {self.request} by {self.by}'


class PaymentReceipt(models.Model):
    payment_request = models.ForeignKey("PaymentRequest", on_delete=models.CASCADE, related_name="receipts")

    file = models.FileField(upload_to=receipt_path, storage=PrivateStorage())

    def __str__(self):
        return os.path.basename(self.file.name)


class PaymentRequestQueryset(models.QuerySet):
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
        return self.filter(status__in=[SUBMITTED, UNDER_REVIEW]).total_value('requested_value')


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
        return self.filter(status__in=[SUBMITTED, UNDER_REVIEW]).total_value('requested_value')


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
    message_for_pm = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    status = models.TextField(choices=REQUEST_STATUS_CHOICES, default=SUBMITTED)

    objects = InvoiceQueryset.as_manager()

    def __str__(self):
        return f'Invoice requested for {self.project}'

    @property
    def has_changes_requested(self):
        return self.status == CHANGES_REQUESTED

    @property
    def status_display(self):
        return self.get_status_display()

    def can_user_delete(self, user):
        if user.is_applicant:
            if self.status in (SUBMITTED, CHANGES_REQUESTED):
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED}:
                return True

        return False

    def can_user_edit(self, user):
        if user.is_applicant:
            if self.status in {SUBMITTED, CHANGES_REQUESTED}:
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED}:
                return True

        return False

    def can_user_change_status(self, user):
        if not user.is_apply_staff:
            return False  # Users can't change status

        if self.status in {PAID, DECLINED}:
            return False

        return True

    @property
    def value(self):
        return self.paid_value or self.amount

    def get_absolute_url(self):
        return reverse('apply:projects:invoices:detail', args=[self.pk])


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


class PaymentRequest(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="payment_requests")
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_requests")

    requested_value = models.DecimalField(
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

    invoice = models.FileField(upload_to=invoice_path, storage=PrivateStorage())
    requested_at = models.DateTimeField(auto_now_add=True)
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    comment = models.TextField(blank=True)
    status = models.TextField(choices=REQUEST_STATUS_CHOICES, default=SUBMITTED)

    objects = PaymentRequestQueryset.as_manager()

    def __str__(self):
        return f'Payment requested for {self.project}'

    @property
    def has_changes_requested(self):
        return self.status == CHANGES_REQUESTED

    @property
    def status_display(self):
        return self.get_status_display()

    def can_user_delete(self, user):
        if user.is_applicant:
            if self.status in (SUBMITTED, CHANGES_REQUESTED):
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED}:
                return True

        return False

    def can_user_edit(self, user):
        if user.is_applicant:
            if self.status in {SUBMITTED, CHANGES_REQUESTED}:
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED}:
                return True

        return False

    def can_user_change_status(self, user):
        if not user.is_apply_staff:
            return False  # Users can't change status

        if self.status in {PAID, DECLINED}:
            return False

        return True

    @property
    def value(self):
        return self.paid_value or self.requested_value

    def get_absolute_url(self):
        return reverse('apply:projects:payments:detail', args=[self.pk])
