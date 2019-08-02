from django import forms
from django.db.models import Q

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.users.groups import STAFF_GROUP_NAME

from .models import Project


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
