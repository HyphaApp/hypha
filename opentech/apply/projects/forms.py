import functools
import os

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q

from addressfield.fields import AddressField
from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.stream_forms.fields import MultiFileField
from opentech.apply.users.groups import STAFF_GROUP_NAME

from .files import get_files
from .models import (
    CHANGES_REQUESTED,
    COMMITTED,
    DECLINED,
    PAID,
    REQUEST_STATUS_CHOICES,
    SUBMITTED,
    UNDER_REVIEW,
    Approval,
    Contract,
    DocumentCategory,
    PacketFile,
    PaymentReceipt,
    PaymentRequest,
    Project
)


User = get_user_model()


def filter_choices(available, choices):
    return [(k, v) for k, v in available if k in choices]


filter_request_choices = functools.partial(filter_choices, REQUEST_STATUS_CHOICES)


class ApproveContractForm(forms.ModelForm):
    name = 'approve_contract_form'

    class Meta:
        fields = ['id']
        model = Contract
        widgets = {'id': forms.HiddenInput()}

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if not self.instance.is_signed:
            raise forms.ValidationError('You can only approve a signed contract')

        super().clean()


class ChangePaymentRequestStatusForm(forms.ModelForm):
    name = 'change_payment_request_status_form'

    class Meta:
        fields = ['status']
        model = PaymentRequest

    def __init__(self, instance, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)

        self.instance = instance

        status_field = self.fields['status']

        if instance.status == SUBMITTED:
            wanted = [CHANGES_REQUESTED, UNDER_REVIEW, DECLINED]
        elif instance.status == CHANGES_REQUESTED:
            wanted = [DECLINED]
        elif instance.status == UNDER_REVIEW:
            wanted = [PAID]
        else:
            wanted = []

        status_field.choices = filter_request_choices(wanted)


class CreateProjectForm(forms.Form):
    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(project__isnull=True),
        widget=forms.HiddenInput(),
        label='',
        required=False,
    )

    def __init__(self, instance=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['submission'].initial = instance.id

    def save(self, *args, **kwargs):
        submission = self.cleaned_data['submission']
        return Project.create_from_submission(submission)


class CreateApprovalForm(forms.ModelForm):
    by = forms.ModelChoiceField(
        queryset=User.objects.approvers(),
        widget=forms.HiddenInput(),
        label='',
        required=False,
    )

    class Meta:
        model = Approval
        fields = ('by',)

    def __init__(self, user=None, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        initial.update(by=user)
        super().__init__(*args, initial=initial, **kwargs)


class EditPaymentRequestForm(forms.ModelForm):
    receipt_list = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(attrs={'checked': 'checked'}))

    name = 'edit_payment_request_form'

    class Meta:
        fields = ['invoice', 'value', 'date_from', 'date_to', 'receipt_list', 'comment']
        model = PaymentRequest
        widgets = {
            'date_from': forms.DateInput,
            'date_to': forms.DateInput,
        }

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)

        self.instance = instance

        self.fields['receipt_list'].choices = [
            (r.pk, os.path.basename(r.file.url))
            for r in instance.receipts.all()
        ]


class ProjectEditForm(forms.ModelForm):
    contact_address = AddressField()

    class Meta:
        fields = [
            'title',
            'contact_legal_name',
            'contact_email',
            'contact_address',
            'contact_phone',
            'value',
            'proposed_start',
            'proposed_end',
        ]
        model = Project
        widgets = {
            'title': forms.TextInput,
            'contact_legal_name': forms.TextInput,
            'contact_email': forms.TextInput,
            'contact_phone': forms.TextInput,
            'proposed_end': forms.DateInput,
            'proposed_start': forms.DateInput,
        }


class ProjectApprovalForm(ProjectEditForm):
    def __init__(self, *args, extra_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        if extra_fields:
            self.fields = {
                **self.fields,
                **extra_fields,
            }

    def save(self, *args, **kwargs):
        self.instance.form_data = {
            field: self.cleaned_data[field]
            for field in self.instance.question_field_ids
            if field in self.cleaned_data
        }
        self.instance.user_has_updated_details = True
        return super().save(*args, **kwargs)


class RejectionForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea)

    def __init__(self, instance=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RemoveDocumentForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        fields = ['id']
        model = PacketFile

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RequestPaymentForm(forms.ModelForm):
    receipts = MultiFileField()

    class Meta:
        fields = ['value', 'invoice', 'date_from', 'date_to', 'receipts', 'comment']
        model = PaymentRequest
        widgets = {
            'date_from': forms.DateInput,
            'date_to': forms.DateInput,
        }

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data['date_from']
        date_to = cleaned_data['date_to']

        if date_from > date_to:
            self.add_error('date_from', 'Date From must be before Date To')

        return cleaned_data

    def save(self, commit=True):
        request = super().save(commit=commit)

        PaymentReceipt.objects.bulk_create(
            PaymentReceipt(payment_request=request, file=receipt)
            for receipt in self.cleaned_data['receipts']
        )

        return request


class SelectDocumentForm(forms.Form):
    category = forms.ModelChoiceField(queryset=DocumentCategory.objects.all())
    files = forms.MultipleChoiceField()

    name = 'select_document_form'

    def __init__(self, existing_files, project, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.project = project

        choices = []
        if existing_files is not None:
            choices = [(f.url, f.filename) for f in existing_files]

        self.fields['files'].choices = choices

    @transaction.atomic()
    def save(self, *args, **kwargs):
        category = self.cleaned_data['category']
        urls = self.cleaned_data['files']

        files = get_files(self.project)
        files = (f for f in files if f.url in urls)

        for f in files:
            new_file = ContentFile(f.read())
            new_file.name = f.filename

            PacketFile.objects.create(
                category=category,
                project=self.project,
                title=f.filename,
                document=new_file,
            )


class SetPendingForm(forms.ModelForm):
    class Meta:
        fields = ['id']
        model = Project
        widgets = {'id': forms.HiddenInput()}

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.instance.status != COMMITTED:
            raise forms.ValidationError('A Project can only be sent for Approval when Committed.')

        if self.instance.is_locked:
            raise forms.ValidationError('A Project can only be sent for Approval once')

        super().clean()

    def save(self, *args, **kwargs):
        self.instance.is_locked = True
        return super().save(*args, **kwargs)


class UploadContractForm(forms.ModelForm):
    class Meta:
        fields = ['file', 'is_signed']
        model = Contract

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not user.is_staff:
            self.fields['is_signed'].widget = forms.HiddenInput()
            self.fields['is_signed'].default = True


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        fields = ['title', 'category', 'document']
        model = PacketFile
        widgets = {'title': forms.TextInput()}

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UpdateProjectLeadForm(forms.ModelForm):
    class Meta:
        fields = ['lead']
        model = Project

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lead_field = self.fields['lead']
        lead_field.label = f'Update lead from {self.instance.lead} to'

        qwargs = Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        lead_field.queryset = (lead_field.queryset.exclude(pk=self.instance.lead_id)
                                                  .filter(qwargs)
                                                  .distinct())
