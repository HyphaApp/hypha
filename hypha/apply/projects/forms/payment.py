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
    APPROVED_BY_FINANCE_1,
    APPROVED_BY_FINANCE_2,
    APPROVED_BY_STAFF,
    CHANGES_REQUESTED_BY_FINANCE_1,
    CHANGES_REQUESTED_BY_FINANCE_2,
    CHANGES_REQUESTED_BY_STAFF,
    CONVERTED,
    DECLINED,
    INVOICE_STATUS_CHOICES,
    PAID,
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
            SUBMITTED: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], user_choices),
            RESUBMITTED: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, APPROVED_BY_STAFF, DECLINED], user_choices),
            CHANGES_REQUESTED_BY_STAFF: filter_request_choices([DECLINED], user_choices),
            APPROVED_BY_STAFF: filter_request_choices(
                [
                    CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1,
                ],
                user_choices
            ),
            CHANGES_REQUESTED_BY_FINANCE_1: filter_request_choices([CHANGES_REQUESTED_BY_STAFF, DECLINED], user_choices),
            APPROVED_BY_FINANCE_1: filter_request_choices([CONVERTED, PAID], user_choices),
            CONVERTED: filter_request_choices([PAID], user_choices),
        }
        if settings.INVOICE_EXTENDED_WORKFLOW:
            possible_status_transitions_lut.update({
                CHANGES_REQUESTED_BY_FINANCE_2: filter_request_choices(
                    [
                        CHANGES_REQUESTED_BY_FINANCE_1, APPROVED_BY_FINANCE_1,
                    ],
                    user_choices
                ),
                APPROVED_BY_FINANCE_1: filter_request_choices([CHANGES_REQUESTED_BY_FINANCE_2, APPROVED_BY_FINANCE_2],
                                                              user_choices),
                APPROVED_BY_FINANCE_2: filter_request_choices([CONVERTED, PAID], user_choices),
            })
        status_field.choices = possible_status_transitions_lut.get(instance.status, [])

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data['status']
        if not self.instance.valid_checks and status == APPROVED_BY_FINANCE_1:
            self.add_error('status', _('Required checks on this invoice need to be compeleted for approval.'))
        return cleaned_data


class InvoiceBaseForm(forms.ModelForm):
    class Meta:
        fields = ['document', 'message_for_pm']
        model = Invoice

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['message_for_pm'] = ''


class CreateInvoiceForm(FileFormMixin, InvoiceBaseForm):
    document = SingleFileField(
        label='Invoice File', required=True,
        help_text=_('The invoice must be a PDF.')
    )
    supporting_documents = MultiFileField(
        required=False,
        help_text=_('Files that are related to the invoice. They could be xls, microsoft office documents, open office documents, pdfs, txt files.')
    )

    field_order = ['document', 'supporting_documents', 'message_for_pm']

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

    field_order = ['document', 'supporting_documents', 'message_for_pm']

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
