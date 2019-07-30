from django import forms

from opentech.apply.funds.models import ApplicationSubmission


class CreateProjectForm(forms.Form):
    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(project__isnull=True),
        widget=forms.HiddenInput(),
    )

    def __init__(self, instance=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['submission'].initial = instance.id
