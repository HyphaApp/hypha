from django import forms

from opentech.apply.funds.models import ApplicationSubmission

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
        project, created = Project.create_from_submission(submission)

        if not created:
            raise forms.ValidationError(
                f'Project for Submission ID={submission.id} already exists',
            )

        return project
