from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.users.groups import STAFF_GROUP_NAME

from ..models.project import COMMITTED, Approval, Contract, PacketFile, Project

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
            raise forms.ValidationError(_('Cannot approve for a different user'))
        return by


class ProjectApprovalForm(forms.ModelForm):
    class Meta:
        fields = [
            'title',
            'value',
            'proposed_start',
            'proposed_end',
            'external_projectid',
        ]
        model = Project
        widgets = {
            'title': forms.TextInput,
            'proposed_end': forms.DateInput,
            'proposed_start': forms.DateInput,
        }

    def __init__(self, *args, extra_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        if extra_fields:
            self.fields = {
                **self.fields,
                **extra_fields,
            }

    def save(self, *args, **kwargs):
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

        if self.instance.is_locked:
            raise forms.ValidationError(_('A Project can only be sent for Approval once'))

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
            "title": _('File Name'),
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
        lead_field.label = _('Update lead from {lead} to').format(lead=self.instance.lead)

        qwargs = Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        lead_field.queryset = (lead_field.queryset.exclude(pk=self.instance.lead_id)
                                                  .filter(qwargs)
                                                  .distinct())
