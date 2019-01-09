from django import forms

from opentech.apply.users.models import User

from .models import ApplicationSubmission, ScreeningStatus
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


class ScreeningSubmissionForm(forms.ModelForm):
    action = forms.ChoiceField(label='Update screening status')

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        # statuses defined in taxonomy ScreeningStatus
        choices = [ ( status.pk, status.title) for status in ScreeningStatus.objects.all() ]
        action_field = self.fields['action']
        action_field.choices = choices
        # TODO: should_show should be calculated such that screening cannot be changed,
        # except by admin if the submission has received a final determination
        self.should_show = bool(choices)


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

    def can_alter_reviewers(self, user):
        return self.instance.stage.has_external_review and user == self.instance.lead

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        reviewers = self.instance.reviewers.all()
        self.submitted_reviewers = User.objects.filter(id__in=self.instance.reviews.values('author'))

        staff_field = self.fields['staff_reviewers']
        staff_field.queryset = staff_field.queryset.exclude(id__in=self.submitted_reviewers)
        staff_field.initial = reviewers

        if self.can_alter_reviewers(self.user):
            review_field = self.fields['reviewer_reviewers']
            review_field.queryset = review_field.queryset.exclude(id__in=self.submitted_reviewers)
            review_field.initial = reviewers
        else:
            self.fields.pop('reviewer_reviewers')

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        if self.can_alter_reviewers(self.user):
            reviewers = self.cleaned_data.get('reviewer_reviewers')
        else:
            reviewers = instance.reviewers_not_reviewed

        instance.reviewers.set(
            self.cleaned_data['staff_reviewers'] |
            reviewers |
            self.submitted_reviewers
        )
        return instance
