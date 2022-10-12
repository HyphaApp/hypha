from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.stream_forms.fields import SingleFileField
from hypha.apply.stream_forms.forms import StreamBaseForm
from hypha.apply.users.groups import STAFF_GROUP_NAME

from ..models.project import (
    COMMITTED,
    PAF_STATUS_CHOICES,
    Contract,
    PacketFile,
    PAFReviewersRole,
    Project,
)

User = get_user_model()


class ApproveContractForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            self.fields['id'].initial = instance.id

    def clean_id(self):
        if self.has_changed():
            raise forms.ValidationError(_('Something changed before your approval please re-review'))

    def clean(self):
        if not self.instance:
            raise forms.ValidationError(_('The contract you were trying to approve has already been approved'))

        if not self.instance.is_signed:
            raise forms.ValidationError(_('You can only approve a signed contract'))

        super().clean()

    def save(self, *args, **kwargs):
        self.instance.save()
        return self.instance


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


class FinalApprovalForm(forms.ModelForm):
    name_prefix = 'final_approval_form'
    final_approval_status = forms.ChoiceField(choices=PAF_STATUS_CHOICES)
    comment = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = Project
        fields = ['final_approval_status', 'comment']

    def __init__(self, instance, user=None, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)


class MixedMetaClass(type(StreamBaseForm), type(forms.ModelForm)):
    pass


class ProjectApprovalForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    class Meta:
        fields = [
            'title',
        ]
        model = Project
        widgets = {
            'title': forms.HiddenInput()
        }

    def __init__(self, *args, extra_fields=None, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['form_data'] = {
            key: value
            for key, value in cleaned_data.items()
            if key not in self._meta.fields
        }
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.form_data = {
            field: self.cleaned_data[field]
            for field in self.instance.question_field_ids
            if field in self.cleaned_data
        }
        self.instance.user_has_updated_details = True
        return super().save(*args, **kwargs)


class ChangePAFStatusForm(forms.ModelForm):
    name_prefix = 'change_paf_status_form'
    paf_reviewers_roles = PAFReviewersRole.objects.all().only('role')
    paf_status = forms.ChoiceField(choices=PAF_STATUS_CHOICES)
    role = forms.ModelChoiceField(queryset=paf_reviewers_roles)
    comment = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        fields = ['paf_status', 'role', 'comment']
        model = Project

    def __init__(self, instance, user, *args, **kwargs):
        super().__init__(instance=instance, *args, **kwargs)


class RemoveDocumentForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        fields = ['id']
        model = PacketFile

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class SetPendingForm(forms.ModelForm):
    class Meta:
        fields = ['id']
        model = Project
        widgets = {'id': forms.HiddenInput()}

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        if self.instance.status != COMMITTED:
            raise forms.ValidationError(_('A Project can only be sent for Approval when Committed.'))

        super().clean()


class UploadContractForm(forms.ModelForm):
    class Meta:
        fields = ['file']
        model = Contract


class StaffUploadContractForm(forms.ModelForm):
    class Meta:
        fields = ['file', 'is_signed']
        model = Contract


class UploadDocumentForm(FileFormMixin, forms.ModelForm):
    document = SingleFileField(label=_('Document'), required=True)

    class Meta:
        fields = ['category', 'document']
        model = PacketFile

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.title = self.instance.document
        return super(UploadDocumentForm, self).save(commit=True)


class UpdateProjectLeadForm(forms.ModelForm):
    class Meta:
        fields = ['lead']
        model = Project

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lead_field = self.fields['lead']
        lead_field.label = _('Update lead from {lead} to').format(lead=self.instance.lead)

        qwargs = Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        lead_field.queryset = (lead_field.queryset.exclude(pk=self.instance.lead_id)
                                                  .filter(qwargs)
                                                  .distinct())
