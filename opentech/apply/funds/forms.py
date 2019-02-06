from django import forms
from django.db.models import Q

from django_select2.forms import Select2Widget

from opentech.apply.users.models import User

from .models import ApplicationSubmission, ApplicationSubmissionReviewer, ReviewerRole
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

    class Meta:
        model = ApplicationSubmission
        fields = ('screening_status',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.should_show = False
        if (self.instance.active and self.user.is_apply_staff) or self.user.is_superuser:
            self.should_show = True


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
    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        reviewers = User.objects.staff() | User.objects.reviewers()
        for role in ReviewerRole.objects.all():
            role_name = role.name.replace(" ", "_")
            field_name = role_name + '_reviewer_' + str(role.pk)
            self.fields[field_name] = forms.ModelChoiceField(
                queryset=reviewers,
                widget=Select2Widget(attrs={'data-placeholder': 'Select a reviewer'}),
                required=False,
            )
            # Pre-populate form field
            existing_submission_reviewer = ApplicationSubmissionReviewer.objects.filter(submission=self.instance, reviewer_role=role)
            if existing_submission_reviewer:
                self.fields[field_name].initial = existing_submission_reviewer[0].reviewer

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        # Loop through self.cleaned_data and save reviewers by role type to submission
        for key, value in self.cleaned_data.items():
            role_pk = key[key.rindex("_")+1:]
            role = ReviewerRole.objects.get(pk=role_pk)
            # Create the reviewer/role association to submission if it doesn't exist
            submission_reviewer, _ = ApplicationSubmissionReviewer.objects.get_or_create(submission=instance, reviewer=value, reviewer_role=role)
            # Delete any reviewer/role associations that existed previously
            ApplicationSubmissionReviewer.objects.filter(
                Q(submission=instance),
                ~Q(reviewer=value),
                Q(reviewer_role=role)).delete()

        return instance


class BatchUpdateReviewersForm(forms.Form):
    staff_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.staff(),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Staff'}),
    )
    submission_ids = forms.CharField(widget=forms.HiddenInput())

    def clean_submission_ids(self):
        value = self.cleaned_data['submission_ids']
        return [int(submission) for submission in value.split(',')]
