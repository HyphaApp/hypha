from django import forms

from opentech.apply.users.models import User

from .models import ApplicationSubmission


class ProgressSubmissionForm(forms.ModelForm):
    action = forms.ChoiceField(label='Take action')

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        choices = [(action, action) for action in self.instance.phase.action_names]
        action_field = self.fields['action']
        action_field.choices = choices
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
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        lead_field = self.fields['lead']
        lead_field.label = f'Update lead from { self.instance.lead } to'
        lead_field.queryset = lead_field.queryset.exclude(id=self.instance.lead.id)


class UpdateReviewersForm(forms.ModelForm):
    staff_reviewers = forms.ModelMultipleChoiceField(queryset=User.objects.staff())
    reviewer_reviewers = forms.ModelmultipleChoiceField(queryset=User.objects.reviewers())

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        # lead_field = self.fields['lead']

    def save(self, *args, **kwargs):
        self.instance.reviewers = self.cleaned_data['staff_reviewers'] + self.cleaned_data['reviewer_reviewers']
        return super().save(*args, **kwargs)
