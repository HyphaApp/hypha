from django import forms

from .models import ApplicationSubmission


class ProgressSubmissionForm(forms.ModelForm):
    action = forms.ChoiceField()

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(action, action) for action in self.instance.phase.action_names]
        self.fields['action'].choices = choices
        self.fields['action'].label = self.instance.phase.name
        self.should_show = bool(choices)

    def save(self, *args, **kwargs):
        new_phase = self.instance.workflow.process(self.instance.phase, self.cleaned_data['action'])
        self.instance.status = str(new_phase)
        return super().save(*args, **kwargs)


class UpdateSubmissionLeadForm(forms.ModelForm):
    class Meta:
        model = ApplicationSubmission
        fields = ('lead',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lead_field = self.fields['lead']
        lead_field.label = f'Update lead from { self.instance.lead } to'
        lead_field.queryset = lead_field.queryset.exclude(id=self.instance.lead.id)
