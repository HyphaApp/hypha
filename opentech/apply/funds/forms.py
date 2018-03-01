from django import forms

from .models import ApplicationSubmission


class ProgressSubmissionForm(forms.ModelForm):
    action = forms.ChoiceField()

    class Meta:
        model = ApplicationSubmission
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(action, action) for action in self.instance.phase.action_names]
        self.fields['action'].choices = choices
        self.fields['action'].label = self.instance.phase.name

    def save(self, *args, **kwargs):
        new_phase = self.instance.workflow.process(self.instance.phase, self.cleaned_data['action'])
        self.instance.status = str(new_phase)
        return super().save(*args, **kwargs)
