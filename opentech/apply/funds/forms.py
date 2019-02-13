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
        queryset=User.objects.reviewers().exclude(id__in=User.objects.staff()),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Reviewers'}),
        label='Reviewers',
        required=False,
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        self.submitted_reviewers = User.objects.filter(id__in=self.instance.reviews.values('author'))
        self.submitted_reviewers = self.submitted_reviewers.exclude(
            id__in=self.instance.assigned.with_roles().values('reviewer'))

        if self.can_alter_external_reviewers(self.instance, self.user):
            reviewers = self.instance.reviewers.all()
            self.prepare_field(
                'reviewer_reviewers',
                initial=reviewers,
                excluded=self.submitted_reviewers
            )
        else:
            self.fields.pop('reviewer_reviewers')

        self.roles = {}
        staff_reviewers = User.objects.staff()

        assigned_roles = {
            assigned.role: assigned.reviewer
            for assigned in self.instance.assigned.filter(
                role__isnull=False
            )
        }

        for role in ReviewerRole.objects.all().order_by('order'):
            field_name = 'reviewer_role_' + slugify(str(role))
            self.roles[field_name] = role

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

            # Move the non-role reviewers field to the end of the field list
            if self.fields.get('reviewer_reviewers'):
                self.fields.move_to_end('reviewer_reviewers')

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

        assigned_roles = {
            role: self.cleaned_data[field]
            for field, role in self.roles.items()
        }

        assigned_staff = instance.staff_not_reviewed.filter(
            assignedreviewers__submission=instance,
            assignedreviewers__role__isnull=True
        ).exclude(
            id__in=[user.id for user in assigned_roles.values() if user]
        )

        if self.can_alter_external_reviewers(self.instance, self.user):
            reviewers = self.cleaned_data.get('reviewer_reviewers')
        else:
            reviewers = instance.reviewers_not_reviewed

        current_reviewers = set(reviewers | self.submitted_reviewers | assigned_staff)

        # Clear out old reviewers, as long as they aren't assigned to a role
        instance.assigned.filter(role=None).exclude(reviewer__in=current_reviewers).delete()

        # Add new reviewers
        reviewers_no_role_existing = instance.reviewers.filter(assignedreviewers__role=None)
        AssignedReviewers.objects.bulk_create(
            AssignedReviewers(
                submission=instance,
                role=None,
                reviewer=reviewer,
            ) for reviewer in current_reviewers
            if reviewer not in reviewers_no_role_existing
        )

        # Update or create role reviewers
        for role, reviewer in assigned_roles.items():
            if reviewer:
                # Edge case: handle any role reviewers that reviewed and now have been removed from role assignment,
                # We want to have a AssignedReviewer record for that orphaned reviewer
                # because they have left a review but no longer have a role
                existing = AssignedReviewers.objects.filter(
                    submission=instance,
                    role=role)
                if existing:
                    existing_reviewer = existing.first().reviewer
                    if existing_reviewer != reviewer:
                        if instance.reviewed_by(existing_reviewer):
                            AssignedReviewers.objects.create(
                                submission=instance,
                                role=None,
                                reviewer=existing_reviewer,
                            )
                        existing.update(reviewer=reviewer)
                else:
                    AssignedReviewers.objects.create(
                        submission=instance,
                        role=role,
                        reviewer=reviewer,
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
