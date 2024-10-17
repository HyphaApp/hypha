import decimal
import os
from textwrap import wrap

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

SUBMITTED = "submitted"
RESUBMITTED = "resubmitted"
CHANGES_REQUESTED_BY_STAFF = "changes_requested_staff"
CHANGES_REQUESTED_BY_FINANCE = "changes_requested_finance_1"
APPROVED_BY_STAFF = "approved_by_staff"
APPROVED_BY_FINANCE = "approved_by_finance_1"
PAID = "paid"
PAYMENT_FAILED = "payment_failed"
DECLINED = "declined"

INVOICE_STATUS_CHOICES = [
    (SUBMITTED, _("Submitted")),
    (RESUBMITTED, _("Resubmitted")),
    (CHANGES_REQUESTED_BY_STAFF, _("Changes requested by staff")),
    (CHANGES_REQUESTED_BY_FINANCE, _("Changes requested by finance")),
    (APPROVED_BY_STAFF, _("Approved by staff")),
    (APPROVED_BY_FINANCE, _("Approved by finance")),
    (PAID, _("Paid")),
    (PAYMENT_FAILED, _("Payment failed")),
    (DECLINED, _("Declined")),
]

# All invoice statuses that allows invoice to be transition directly to RESUBMITTED.
INVOICE_TRANISTION_TO_RESUBMITTED = [
    SUBMITTED,
    RESUBMITTED,
    CHANGES_REQUESTED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
]

INVOICE_STATUS_PM_CHOICES = [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED]
INVOICE_STATUS_FINANCE_1_CHOICES = [
    CHANGES_REQUESTED_BY_FINANCE,
    APPROVED_BY_FINANCE,
    DECLINED,
    PAID,
    PAYMENT_FAILED,
]


def invoice_status_user_choices(user):
    if user.is_finance:
        return INVOICE_STATUS_FINANCE_1_CHOICES
    if user.is_apply_staff:
        return INVOICE_STATUS_PM_CHOICES
    return []


def invoice_path(instance, filename):
    return f"projects/{instance.project_id}/payment_invoices/{filename}"


class InvoiceQueryset(models.QuerySet):
    def in_progress(self):
        return self.exclude(status__in=[DECLINED, PAID])

    def approved_by_staff(self):
        return self.filter(status=APPROVED_BY_STAFF)

    def approved_by_finance_1(self):
        return self.filter(status=APPROVED_BY_FINANCE)

    def waiting_to_convert(self):
        return self.filter(status=APPROVED_BY_FINANCE)

    def for_finance_1(self):
        return self.filter(status__in=[APPROVED_BY_STAFF, APPROVED_BY_FINANCE])

    def rejected(self):
        return self.filter(status=DECLINED).order_by("-requested_at")

    def not_rejected(self):
        return self.exclude(status=DECLINED).order_by("-requested_at")

    def total_value(self, field):
        return self.aggregate(
            total=Coalesce(Sum(field), Value(0), output_field=models.DecimalField())
        )["total"]

    def paid_value(self):
        return self.filter(status=PAID).total_value("paid_value")

    def unpaid_value(self):
        return self.filter(~Q(status=PAID)).total_value("paid_value")


class InvoiceDeliverable(models.Model):
    deliverable = models.ForeignKey(
        "Deliverable", on_delete=models.CASCADE, related_name="deliverables"
    )
    quantity = models.IntegerField(
        help_text=_("Quantity Selected on an Invoice"), default=0
    )

    wagtail_reference_index_ignore = True

    def __str__(self):
        return self.deliverable.name

    def get_absolute_api_url(self):
        return reverse(
            "api:v1:remove-deliverables", kwargs={"pk": self.pk, "invoice_pk": self.pk}
        )


class Invoice(models.Model):
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, related_name="invoices"
    )
    by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices"
    )
    paid_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal("0.01"))],
        null=True,
    )
    document = models.FileField(upload_to=invoice_path, storage=PrivateStorage())
    requested_at = models.DateTimeField(auto_now_add=True)
    message_for_pm = models.TextField(blank=True, verbose_name=_("Message"))
    comment = models.TextField(blank=True)
    invoice_number = models.CharField(
        max_length=50, null=True, verbose_name=_("Invoice number")
    )
    invoice_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(decimal.Decimal("0.01"))],
        null=True,
        verbose_name=_("Invoice amount"),
    )
    invoice_date = models.DateField(null=True, verbose_name=_("Invoice date"))
    paid_date = models.DateField(null=True, verbose_name=_("Paid date"))
    status = FSMField(default=SUBMITTED, choices=INVOICE_STATUS_CHOICES)
    deliverables = ManyToManyField("InvoiceDeliverable", related_name="invoices")
    objects = InvoiceQueryset.as_manager()

    wagtail_reference_index_ignore = True

    def __str__(self):
        return _("Invoice requested for {project}").format(project=self.project)

    @transition(
        field=status, source=INVOICE_TRANISTION_TO_RESUBMITTED, target=RESUBMITTED
    )
    def transition_invoice_to_resubmitted(self):
        """
        Tranistion invoice to resubmitted status.
        This method generally gets used on invoice edit.
        """
        pass

    @property
    def has_changes_requested(self):
        return self.status == CHANGES_REQUESTED_BY_STAFF

    @property
    def status_display(self):
        return self.get_status_display()

    @property
    def vendor_document_number(self):
        """
        Vendor document number is a required field to create invoices in IntAcct.

        Formatting should be HP###### i.e. HP000001 and so on.
        """
        prefix = "HP-"
        return prefix + "-".join(wrap(f"{self.id:06}", 3))

    def can_user_delete(self, user):
        if user.is_applicant or user.is_apply_staff:
            if self.status in (SUBMITTED):
                return True

        return False

    def can_user_edit(self, user):
        """
        Check when an user can edit an invoice.
        Only applicant and staff have permission to edit invoice based on its current status.
        """
        if user.is_applicant:
            if self.status in {SUBMITTED, CHANGES_REQUESTED_BY_STAFF, RESUBMITTED}:
                return True

        if user.is_apply_staff:
            if self.status in {SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE}:
                return True

        return False

    def can_user_change_status(self, user):
        """
        Check user roles that can tranistion invoice status based on the current status.
        """
        if not (user.is_contracting or user.is_apply_staff or user.is_finance):
            return False  # Users can't change status

        if self.status in {DECLINED}:
            return False

        if user.is_contracting:
            if self.status in {SUBMITTED, CHANGES_REQUESTED_BY_STAFF, RESUBMITTED}:
                return True

        if user.is_apply_staff:
            if self.status in {
                SUBMITTED,
                RESUBMITTED,
                CHANGES_REQUESTED_BY_STAFF,
                CHANGES_REQUESTED_BY_FINANCE,
            }:
                return True

        if user.is_finance:
            if self.status in {
                APPROVED_BY_STAFF,
                APPROVED_BY_FINANCE,
                PAID,
                PAYMENT_FAILED,
            }:
                return True

        return False

    def can_user_edit_deliverables(self, user):
        if not (user.is_apply_staff or user.is_finance):
            return False
        if user.is_apply_staff:
            if self.status in {SUBMITTED, RESUBMITTED, CHANGES_REQUESTED_BY_FINANCE}:
                return True
        if user.is_finance:
            if self.status in {APPROVED_BY_STAFF}:
                return True
        return False

    @property
    def value(self):
        return self.paid_value

    def get_absolute_url(self):
        return reverse(
            "apply:projects:invoice-detail",
            kwargs={"pk": self.project.pk, "invoice_pk": self.pk},
        )

    @property
    def deliverables_total_amount(self):
        return self.deliverables.all().aggregate(
            total=Sum(
                F("deliverable__unit_price") * F("quantity"), output_field=FloatField()
            )
        )

    @property
    def filename(self):
        return os.path.basename(self.document.name)


class SupportingDocument(models.Model):
    wagtail_reference_index_ignore = True

    document = models.FileField(
        upload_to="supporting_documents", storage=PrivateStorage()
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="supporting_documents",
    )

    def __str__(self):
        return "{invoice}".format(invoice=self.invoice) + " -> " + self.document.name

    @property
    def filename(self):
        return os.path.basename(self.document.name)
