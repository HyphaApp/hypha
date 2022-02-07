import json

from django import forms
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.stream_forms.fields import MultiFileField, SingleFileField

from ..models.payment import (
    APPROVED_BY_FINANCE_1,
    APPROVED_BY_FINANCE_2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE_1,
    CHANGES_REQUESTED_BY_FINANCE_2,
    CHANGES_REQUESTED_BY_STAFF,
    DECLINED,
    INVOICE_STATUS_CHOICES,
    RESUBMITTED,
    SUBMITTED,
    Invoice,
    SupportingDocument,
    invoice_status_user_choices,
)
from ..models.project import PacketFile


def filter_request_choices(choices, user_choices):
    return [(k, v) for k, v in INVOICE_STATUS_CHOICES if k in choices and k in user_choices]


class ChangeInvoiceStatusForm(forms.ModelForm):
    name_prefix = 'change_invoice_status_form'

    class Meta:
        fields = ['status', 'comment']
        model = Invoice

    def __init__(self, instance, user, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)
        self.initial['comment'] = ''
        status_field = self.fields['status']
        user_choices = invoice_status_user_choices(user)
        possible_status_transitions_lut = {
            CHANGES_REQUESTED_BY_STAFF: filter_request_choices([DECLINED], user_choices),
            CHANGES_REQUESTED_BY_FINANCE_1: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, DECLINED], user_choices),
            CHANGES_REQUESTED_BY_FINANCE_2: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, DECLINED], user_choices),
            SUBMITTED: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], user_choices),
            RESUBMITTED: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], user_choices),
            APPROVED_BY_STAFF: filter_request_choices(
                [
                    CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1, DECLINED,
                    CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2
                ],
                user_choices
            ),
            APPROVED_BY_FINANCE_1: filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2, DECLINED], user_choices),
        }
        status_field.choices = possible_status_transitions_lut.get(instance.status, [])


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
