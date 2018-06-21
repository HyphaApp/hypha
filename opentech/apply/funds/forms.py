from django import forms
from django_fsm import can_proceed

from opentech.apply.users.models import User

from .models import ApplicationSubmission
from .widgets import Select2MultiCheckboxesWidget


class ProgressSubmissionForm(forms.ModelForm):
    action = forms.ChoiceField(label='Take action')

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        choices = list(self.instance.get_actions_for_user(self.user))
        action_field = self.fields['action']
        action_field.choices = choices
        self.should_show = bool(choices)

    def clean_action(self):
        action_name = self.cleaned_data['action']
        transition = self.instance.get_transition(action_name)
        if not can_proceed(transition):
            action = self.instance.phase.transitions[action_name]
            raise forms.ValidationError(f'You do not have permission to "{ action }"')
        return action_name


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
    staff_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.staff(),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Staff'}),
        required=False,
    )
    reviewer_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.reviewers().exclude(id__in=User.objects.staff()),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Reviewers'}),
        label='Reviewers',
        required=False,
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        reviewers = self.instance.reviewers.all()
        self.submitted_reviewers = User.objects.filter(id__in=self.instance.reviews.values('author'))

        staff_field = self.fields['staff_reviewers']
        staff_field.queryset = staff_field.queryset.exclude(id__in=self.submitted_reviewers)
        staff_field.initial = reviewers

        if self.instance.stage.has_external_review and user == self.instance.lead:
            review_field = self.fields['reviewer_reviewers']
            review_field.queryset = review_field.queryset.exclude(id__in=self.submitted_reviewers)
            review_field.initial = reviewers
        else:
            self.fields.pop('reviewer_reviewers')

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.reviewers.set(
            self.cleaned_data['staff_reviewers'] |
            self.cleaned_data.get('reviewer_reviewers', User.objects.none()) |
            self.submitted_reviewers
        )
        return instance
