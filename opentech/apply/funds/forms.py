from django import forms
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from opentech.apply.users.models import User

from .models import ApplicationSubmission, AssignedReviewers, ReviewerRole
from .widgets import Select2MultiCheckboxesWidget, Select2IconWidget


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
        if self.user.is_apply_staff:
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
    reviewer_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.reviewers().only('pk', 'full_name'),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Reviewers'}),
        label='Reviewers',
        required=False,
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        assigned_roles = {
            assigned.role: assigned.reviewer
            for assigned in self.instance.assigned.filter(
                role__isnull=False
            )
        }

        staff_reviewers = User.objects.staff().only('full_name', 'pk')

        self.role_fields = {}
        for role in ReviewerRole.objects.all().order_by('order'):
            field_name = 'role_reviewer_' + slugify(str(role))
            self.role_fields[field_name] = role

            self.fields[field_name] = forms.ModelChoiceField(
                queryset=staff_reviewers,
                widget=Select2IconWidget(attrs={
                    'data-placeholder': 'Select a reviewer', 'icon': role.icon
                }),
                required=False,
                label=f'{role.name} Reviewer',
            )
            # Pre-populate form field
            self.fields[field_name].initial = assigned_roles.get(role)

        self.submitted_reviewers = User.objects.filter(
            id__in=self.instance.reviews.values('author'),
        )

        if self.can_alter_external_reviewers(self.instance, self.user):

            reviewers = self.instance.reviewers.all().only('pk')
            self.prepare_field(
                'reviewer_reviewers',
                initial=reviewers,
                excluded=self.submitted_reviewers
            )

            # Move the non-role reviewers field to the end of the field list
            self.fields.move_to_end('reviewer_reviewers')
        else:
            self.fields.pop('reviewer_reviewers')

    def prepare_field(self, field_name, initial, excluded):
        field = self.fields[field_name]
        field.queryset = field.queryset.exclude(id__in=excluded)
        field.initial = initial

    def can_alter_external_reviewers(self, instance, user):
        return instance.stage.has_external_review and (user == instance.lead or user.is_superuser)

    def clean(self):
        cleaned_data = super().clean()
        role_reviewers = [
            user
            for field, user in self.cleaned_data.items()
            if field != 'reviewer_reviewers'
        ]

        # If any of the users match and are set to multiple roles, throw an error
        if len(role_reviewers) != len(set(role_reviewers)) and any(role_reviewers):
            self.add_error(None, _('Users cannot be assigned to multiple roles.'))

        return cleaned_data

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        """
        1. Update role reviewers
        2. Update non-role reviewers
            2a. Remove those not on form
            2b. Add in any new non-role reviewers selected
        3. Add in anyone who has already reviewed but who is not selected as a reviewer on the form
        """

        # 1. Update role reviewers
        assigned_roles = {
            role: self.cleaned_data[field]
            for field, role in self.role_fields.items()
        }
        for role, reviewer in assigned_roles.items():
            if reviewer:
                AssignedReviewers.objects.update_or_create(
                    submission=instance,
                    role=role,
                    defaults={'reviewer': reviewer},
                )

        # 2. Update non-role reviewers
        # 2a. Remove those not on form
        if self.can_alter_external_reviewers(self.instance, self.user):
            reviewers = self.cleaned_data.get('reviewer_reviewers')
            assigned_reviewers = instance.assigned.without_roles()
            assigned_reviewers.exclude(
                reviewer__in=reviewers | self.submitted_reviewers
            ).delete()

            remaining_reviewers = assigned_reviewers.values_list('reviewer_id', flat=True)

            # 2b. Add in any new non-role reviewers selected
            AssignedReviewers.objects.bulk_create(
                AssignedReviewers(
                    submission=instance,
                    role=None,
                    reviewer=reviewer
                ) for reviewer in reviewers
                if reviewer.id not in remaining_reviewers
            )

        # 3. Add in anyone who has already reviewed but who is not selected as a reviewer on the form
        orphaned_reviews = instance.reviews.exclude(
            author__in=instance.assigned.values('reviewer')
        ).select_related('author')

        AssignedReviewers.objects.bulk_create(
            AssignedReviewers(
                submission=instance,
                role=None,
                reviewer=review.author
            ) for review in orphaned_reviews
        )

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
