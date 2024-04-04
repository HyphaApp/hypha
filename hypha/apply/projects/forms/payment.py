import json

from django import forms
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.stream_forms.fields import MultiFileField, SingleFileField

from ..models.payment import (
    APPROVED_BY_FINANCE,
    APPROVED_BY_FINANCE_2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE,
    CHANGES_REQUESTED_BY_FINANCE_2,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    INVOICE_STATUS_CHOICES,
    PAID,
    PAYMENT_FAILED,
    RESUBMITTED,
    SUBMITTED,
    Invoice,
    SupportingDocument,
    invoice_status_user_choices,
)
from ..models.project import PacketFile
from ..utils import get_invoice_status_display_value


def filter_request_choices(choices, user_choices):
    return [
        (k, v) for k, v in INVOICE_STATUS_CHOICES if k in choices and k in user_choices
    ]


def get_invoice_possible_transition_for_user(user, invoice):
    user_choices = invoice_status_user_choices(user)
    possible_status_transitions_lut = {
        SUBMITTED: filter_request_choices(
            [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], user_choices
        ),
        RESUBMITTED: filter_request_choices(
            [CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], user_choices
        ),
        CHANGES_REQUESTED_BY_STAFF: filter_request_choices([DECLINED], user_choices),
        APPROVED_BY_STAFF: filter_request_choices(
            [
                CHANGES_REQUESTED_BY_FINANCE,
                APPROVED_BY_FINANCE,
            ],
            user_choices,
        ),
        CHANGES_REQUESTED_BY_FINANCE: filter_request_choices(
            [CHANGES_REQUESTED_BY_STAFF, DECLINED], user_choices
        ),
        APPROVED_BY_FINANCE: filter_request_choices([PAID], user_choices),
        PAID: filter_request_choices([PAYMENT_FAILED], user_choices),
        PAYMENT_FAILED: filter_request_choices([PAID], user_choices),
    }
    if settings.INVOICE_EXTENDED_WORKFLOW:
        possible_status_transitions_lut.update(
            {
                CHANGES_REQUESTED_BY_FINANCE_2: filter_request_choices(
                    [
                        CHANGES_REQUESTED_BY_FINANCE,
                        APPROVED_BY_FINANCE,
                    ],
                    user_choices,
                ),
                APPROVED_BY_FINANCE: filter_request_choices(
                    [CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2],
                    user_choices,
                ),
                APPROVED_BY_FINANCE_2: filter_request_choices([PAID], user_choices),
            }
        )
    return possible_status_transitions_lut.get(invoice.status, [])


class ChangeInvoiceStatusForm(forms.ModelForm):
    name_prefix = "change_invoice_status_form"

    class Meta:
        fields = ["status", "comment"]
        model = Invoice

    def __init__(self, instance, user, *args, **kwargs):
        super().__init__(*args, **kwargs, instance=instance)
        self.initial["comment"] = ""
        status_field = self.fields["status"]

        status_field.choices = get_invoice_possible_transition_for_user(
            user, invoice=instance
        )


class InvoiceBaseForm(forms.ModelForm):
    class Meta:
        fields = ["invoice_number", "invoice_amount", "document", "message_for_pm"]
        model = Invoice

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["message_for_pm"] = ""


class CreateInvoiceForm(FileFormMixin, InvoiceBaseForm):
    document = SingleFileField(
        label=_("Invoice file"),
        required=True,
        help_text=_("The invoice must be a PDF."),
    )
    supporting_documents = MultiFileField(
        required=False,
        help_text=_(
            "Files that are related to the invoice. They could be xls, microsoft office documents, open office documents, pdfs, txt files."
        ),
    )

    field_order = [
        "invoice_number",
        "invoice_amount",
        "document",
        "supporting_documents",
        "message_for_pm",
    ]

    def save(self, commit=True):
        invoice = super().save(commit=commit)

        supporting_documents = self.cleaned_data["supporting_documents"] or []

        SupportingDocument.objects.bulk_create(
            SupportingDocument(invoice=invoice, document=document)
            for document in supporting_documents
        )

        return invoice


class EditInvoiceForm(FileFormMixin, InvoiceBaseForm):
    document = SingleFileField(label=_("Invoice File"), required=True)
    supporting_documents = MultiFileField(required=False)

    field_order = [
        "invoice_number",
        "invoice_amount",
        "document",
        "supporting_documents",
        "message_for_pm",
    ]

    @transaction.atomic
    def save(self, commit=True):
        invoice = super().save(commit=commit)
        not_deleted_original_filenames = [
            file["name"]
            for file in json.loads(self.cleaned_data["supporting_documents-uploads"])
        ]
        for f in invoice.supporting_documents.all():
            if f.document.name not in not_deleted_original_filenames:
                f.document.delete()
                f.delete()

        for f in self.cleaned_data["supporting_documents"]:
            if not isinstance(f, FieldFile):
                try:
                    SupportingDocument.objects.create(invoice=invoice, document=f)
                finally:
                    f.close()
        return invoice


class SelectDocumentForm(forms.ModelForm):
    document = forms.ChoiceField(
        label=_("Document"), widget=forms.Select(attrs={"id": "from_submission"})
    )

    class Meta:
        model = PacketFile
        fields = ["category", "document"]

    def __init__(self, existing_files, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.files = existing_files

        choices = [(f.url, f.filename) for f in self.files]

        self.fields["document"].choices = choices

    def clean_document(self):
        file_url = self.cleaned_data["document"]
        for file in self.files:
            if file.url == file_url:
                new_file = ContentFile(file.read())
                new_file.name = file.filename
                return new_file
        raise forms.ValidationError(_("File not found on submission"))

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class BatchUpdateInvoiceStatusForm(forms.Form):
    invoice_action = forms.ChoiceField(label=_("Status"))
    invoices = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "js-invoices-id"})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        if self.user.is_apply_staff:
            self.fields["invoice_action"].choices = [
                (DECLINED, get_invoice_status_display_value(DECLINED))
            ]
        elif self.user.is_finance:
            self.fields["invoice_action"].choices = [
                (DECLINED, get_invoice_status_display_value(DECLINED)),
                (PAID, get_invoice_status_display_value(PAID)),
                (PAYMENT_FAILED, get_invoice_status_display_value(PAYMENT_FAILED)),
            ]

    def clean_invoices(self):
        value = self.cleaned_data["invoices"]
        invoice_ids = [int(invoice) for invoice in value.split(",")]
        return Invoice.objects.filter(id__in=invoice_ids)
