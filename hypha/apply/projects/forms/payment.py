import functools
import json

from django import forms
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.stream_forms.fields import MultiFileField, SingleFileField

from ..models.payment import (
    APPROVED_BY_FINANCE1,
    APPROVED_BY_FINANCE2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED,
    CHANGES_REQUESTED_BY_FINANCE1,
    DECLINED,
    PAID,
    REQUEST_STATUS_CHOICES,
    RESUBMITTED,
    SUBMITTED,
    Invoice,
    SupportingDocument,
)
from ..models.project import PacketFile


def filter_choices(available, choices):
    return [(k, v) for k, v in available if k in choices]


filter_request_choices = functools.partial(filter_choices, REQUEST_STATUS_CHOICES)


class ChangeInvoiceStatusForm(forms.ModelForm):
    name_prefix = 'change_invoice_status_form'

    class Meta:
        fields = ['status', 'comment', 'paid_value']
        model = Invoice

    def __init__(self, instance, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)

        self.initial['paid_value'] = self.instance.amount
        self.initial['comment'] = ''

        status_field = self.fields['status']

        possible_status_transitions_lut = {
            CHANGES_REQUESTED: filter_request_choices([DECLINED]),
            CHANGES_REQUESTED_BY_FINANCE1: filter_request_choices([CHANGES_REQUESTED, DECLINED]),
            SUBMITTED: filter_request_choices([CHANGES_REQUESTED, APPROVED_BY_STAFF, DECLINED]),
            RESUBMITTED: filter_request_choices([CHANGES_REQUESTED, APPROVED_BY_STAFF, DECLINED]),
            APPROVED_BY_FINANCE1: filter_request_choices([CHANGES_REQUESTED, APPROVED_BY_FINANCE2, DECLINED]),
            APPROVED_BY_STAFF: filter_request_choices([CHANGES_REQUESTED_BY_FINANCE1, APPROVED_BY_FINANCE1, DECLINED]),
        }
        status_field.choices = possible_status_transitions_lut.get(instance.status, [])

        if instance.status != APPROVED_BY_FINANCE2:
            del self.fields['paid_value']

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data['status']
        paid_value = cleaned_data.get('paid_value')

        if paid_value and status != PAID:
            self.add_error('paid_value', _('You can only set a value when moving to the Paid status.'))
        return cleaned_data


class InvoiceBaseForm(forms.ModelForm):
    class Meta:
        fields = ['date_from', 'date_to', 'amount', 'document', 'message_for_pm']
        model = Invoice
        widgets = {
            'date_from': forms.DateInput,
            'date_to': forms.DateInput,
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs['min'] = 0
        self.initial['message_for_pm'] = ''

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data['date_from']
        date_to = cleaned_data['date_to']

        if date_from > date_to:
            self.add_error('date_from', _('Date From must be before Date To'))

        return cleaned_data


class CreateInvoiceForm(FileFormMixin, InvoiceBaseForm):
    document = SingleFileField(label='Invoice File', required=True)
    supporting_documents = MultiFileField(
        required=False,
        help_text=_('Files that are related to the invoice. They could be xls, microsoft office documents, open office documents, pdfs, txt files.')
    )

    field_order = ['date_from', 'date_to', 'amount', 'document', 'supporting_documents', 'message_for_pm']

    def save(self, commit=True):
        invoice = super().save(commit=commit)

        supporting_documents = self.cleaned_data['supporting_documents'] or []

        SupportingDocument.objects.bulk_create(
            SupportingDocument(invoice=invoice, document=document)
            for document in supporting_documents
        )

        return invoice


class EditInvoiceForm(FileFormMixin, InvoiceBaseForm):
    document = SingleFileField(label=_('Invoice File'), required=True)
    supporting_documents = MultiFileField(required=False)

    field_order = ['date_from', 'date_to', 'amount', 'document', 'supporting_documents', 'message_for_pm']

    @transaction.atomic
    def save(self, commit=True):
        invoice = super().save(commit=commit)
        not_deleted_original_filenames = [
            file['name'] for file in json.loads(self.cleaned_data['supporting_documents-uploads'])
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
        label="Document",
        widget=forms.Select(attrs={'id': 'from_submission'})
    )

    class Meta:
        model = PacketFile
        fields = ['category', 'document']

    def __init__(self, existing_files, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.files = existing_files

        choices = [(f.url, f.filename) for f in self.files]

        self.fields['document'].choices = choices

    def clean_document(self):
        file_url = self.cleaned_data['document']
        for file in self.files:
            if file.url == file_url:
                new_file = ContentFile(file.read())
                new_file.name = file.filename
                return new_file
        raise forms.ValidationError(_('File not found on submission'))

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
