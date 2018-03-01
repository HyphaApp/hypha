from django import forms

from .models import ApplicationSubmission


class ProgressSubmissionForm(forms.ModelForm):
    class Meta:
        model = ApplicationSubmission
        fields = ('status',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
