import functools

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from addressfield.fields import AddressField
from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.stream_forms.fields import MultiFileField
from hypha.apply.users.groups import STAFF_GROUP_NAME
from hypha.apply.utils.fields import RichTextField

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
    PacketFile,
    PaymentReceipt,
    PaymentRequest,
    Project,
    Report,
    ReportConfig,
    ReportPrivateFiles,
    ReportVersion,
)

User = get_user_model()


def filter_choices(available, choices):
    return [(k, v) for k, v in available if k in choices]


filter_request_choices = functools.partial(filter_choices, REQUEST_STATUS_CHOICES)


class ApproveContractForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            self.fields['id'].initial = instance.id

    def clean_id(self):
        if self.has_changed():
            raise forms.ValidationError('Something changed before your approval please re-review')

    def clean(self):
        if not self.instance:
            raise forms.ValidationError('The contract you were trying to approve has already been approved')

        if not self.instance.is_signed:
            raise forms.ValidationError('You can only approve a signed contract')

        super().clean()

    def save(self, *args, **kwargs):
        self.instance.save()
        return self.instance


class ChangePaymentRequestStatusForm(forms.ModelForm):
    name_prefix = 'change_payment_request_status_form'

    class Meta:
        fields = ['status', 'comment', 'paid_value']
        model = PaymentRequest

    def __init__(self, instance, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)

        self.initial['paid_value'] = self.instance.requested_value

        status_field = self.fields['status']

        possible_status_transitions_lut = {
            CHANGES_REQUESTED: filter_request_choices([DECLINED]),
            SUBMITTED: filter_request_choices([CHANGES_REQUESTED, UNDER_REVIEW, DECLINED]),
            UNDER_REVIEW: filter_request_choices([PAID]),
        }
        status_field.choices = possible_status_transitions_lut.get(instance.status, [])

        if instance.status != UNDER_REVIEW:
            del self.fields['paid_value']

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data['status']
        paid_value = cleaned_data.get('paid_value')

        if paid_value and status != PAID:
            self.add_error('paid_value', 'You can only set a value when moving to the Paid status.')
        return cleaned_data


class CreateProjectForm(forms.Form):
    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(project__isnull=True),
        widget=forms.HiddenInput(),
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
    )

    class Meta:
        model = Approval
        fields = ('by',)

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_by(self):
        by = self.cleaned_data['by']
        if by != self.user:
            raise forms.ValidationError('Cannot approve for a different user')
        return by


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


class PaymentRequestBaseForm(forms.ModelForm):
    class Meta:
        fields = ['requested_value', 'invoice', 'date_from', 'date_to']
        model = PaymentRequest
        widgets = {
            'date_from': forms.DateInput,
            'date_to': forms.DateInput,
        }
        labels = {
            'requested_value': 'Requested Value ($)'
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['requested_value'].widget.attrs['min'] = 0

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data['date_from']
        date_to = cleaned_data['date_to']

        if date_from > date_to:
            self.add_error('date_from', 'Date From must be before Date To')

        return cleaned_data


class CreatePaymentRequestForm(PaymentRequestBaseForm):
    receipts = MultiFileField()

    def save(self, commit=True):
        request = super().save(commit=commit)

        PaymentReceipt.objects.bulk_create(
            PaymentReceipt(payment_request=request, file=receipt)
            for receipt in self.cleaned_data['receipts']
        )

        return request


class EditPaymentRequestForm(PaymentRequestBaseForm):
    receipt_list = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'delete'}),
        queryset=PaymentReceipt.objects.all(),
        required=False,
        label='Receipts'
    )
    receipts = MultiFileField(label='', required=False)

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)

        self.fields['receipt_list'].queryset = instance.receipts.all()

        self.fields['requested_value'].label = 'Value'

    @transaction.atomic
    def save(self, commit=True):
        request = super().save(commit=commit)

        removed_receipts = self.cleaned_data['receipt_list']

        removed_receipts.delete()

        to_add = self.cleaned_data['receipts']
        if to_add:
            PaymentReceipt.objects.bulk_create(
                PaymentReceipt(payment_request=request, file=receipt)
                for receipt in to_add
            )
        return request


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
        raise forms.ValidationError("File not found on submission")

    @transaction.atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


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
        fields = ['file']
        model = Contract


class StaffUploadContractForm(forms.ModelForm):
    class Meta:
        fields = ['file', 'is_signed']
        model = Contract


class UploadDocumentForm(forms.ModelForm):
    class Meta:
        fields = ['title', 'category', 'document']
        model = PacketFile
        widgets = {'title': forms.TextInput()}
        labels = {
            "title": "File Name",
        }

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


class ReportEditForm(forms.ModelForm):
    public_content = RichTextField(
        help_text="This section of the report will be shared with the broader community."
    )
    private_content = RichTextField(
        help_text="This section of the report will be shared with staff only."
    )
    file_list = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'delete'}),
        queryset=ReportPrivateFiles.objects.all(),
        required=False,
        label='Files'
    )
    files = MultiFileField(required=False, label='')

    class Meta:
        model = Report
        fields = (
            'public_content',
            'private_content',
            'file_list',
            'files',
        )

    def __init__(self, *args, user=None, initial={}, **kwargs):
        self.report_files = initial.pop(
            'file_list',
            ReportPrivateFiles.objects.none(),
        )
        super().__init__(*args, initial=initial, **kwargs)
        self.fields['file_list'].queryset = self.report_files
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        public = cleaned_data['public_content']
        private = cleaned_data['private_content']
        if not private and not public:
            missing_content = 'Must include either public or private content when submitting a report.'
            self.add_error('public_content', missing_content)
            self.add_error('private_content', missing_content)
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        is_draft = 'save' in self.data

        version = ReportVersion.objects.create(
            report=self.instance,
            public_content=self.cleaned_data['public_content'],
            private_content=self.cleaned_data['private_content'],
            submitted=timezone.now(),
            draft=is_draft,
            author=self.user,
        )

        if is_draft:
            self.instance.draft = version
        else:
            # If this is the first submission of the report we track that as the
            # submitted date of the report
            if not self.instance.submitted:
                self.instance.submitted = version.submitted
            self.instance.current = version
            self.instance.draft = None

        instance = super().save(commit)

        removed_files = self.cleaned_data['file_list']
        ReportPrivateFiles.objects.bulk_create(
            ReportPrivateFiles(report=version, document=file.document)
            for file in self.report_files
            if file not in removed_files
        )

        added_files = self.cleaned_data['files']
        if added_files:
            ReportPrivateFiles.objects.bulk_create(
                ReportPrivateFiles(report=version, document=file)
                for file in added_files
            )

        return instance


class ReportFrequencyForm(forms.ModelForm):
    start = forms.DateField(label='Starting on:')

    class Meta:
        model = ReportConfig
        fields = ('occurrence', 'frequency', 'start')
        labels = {
            'occurrence': 'No.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        last_report = self.instance.last_report()

        self.fields['start'].widget.attrs.update({
            'min': max(
                last_report.end_date if last_report else today,
                today,
            ),
            'max': self.instance.project.end_date,
        })

    def clean_start(self):
        start_date = self.cleaned_data['start']
        last_report = self.instance.last_report()
        if last_report and start_date <= last_report.end_date:
            raise ValidationError(
                _("Cannot start a schedule before the current reporting period"),
                code="bad_start"
            )

        if start_date < timezone.now().date():
            raise ValidationError(
                _("Cannot start a schedule in the past"),
                code="bad_start"
            )

        if start_date > self.instance.project.end_date:
            raise ValidationError(
                _("Cannot start a schedule beyond the end date"),
                code="bad_start"
            )
        return start_date

    def save(self, *args, **kwargs):
        self.instance.schedule_start = self.cleaned_data['start']
        return super().save(*args, **kwargs)
