from functools import partial
from itertools import groupby
from operator import methodcaller

import bleach
from django import forms
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from hypha.apply.categories.models import MetaTerm
from hypha.apply.users.models import User

from .models import (
    ApplicationSubmission,
    AssignedReviewers,
    Reminder,
    ReviewerRole,
    ScreeningStatus,
)
from .utils import render_icon
from .widgets import MetaTermSelect2Widget, Select2MultiCheckboxesWidget
from .workflow import get_action_mapping


class ApplicationSubmissionModelForm(forms.ModelForm):
    """
    Application Submission model's save method performs several operations
    which are not required in forms which update fields like status, partners etc.
    It also has a side effect of creating a new file uploads every time with long filenames (#1572).
    """

    def save(self, commit=True):
        """
        Save this form's self.instance object if commit=True. Otherwise, add
        a save_m2m() method to the form which can be called after the instance
        is saved manually at a later time. Return the model instance.
        https://github.com/django/django/blob/5d9cf79baf07fc4aed7ad1b06990532a65378155/django/forms/models.py#L444
        """
        if self.errors:
            raise ValueError(
                "The %s could not be %s because the data didn't validate." % (
                    self.instance._meta.object_name,
                    'created' if self.instance._state.adding else 'changed',
                )
            )
        if commit:
            # If committing, save the instance and the m2m data immediately.
            self.instance.save(skip_custom=True)
            self._save_m2m()
        else:
            # If not committing, add a method to the form to allow deferred
            # saving of m2m data.
            self.save_m2m = self._save_m2m
        return self.instance


class ProgressSubmissionForm(ApplicationSubmissionModelForm):
    action = forms.ChoiceField(label=_('Take action'))

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        choices = list(self.instance.get_actions_for_user(self.user))
        # Sort the transitions by the order they are listed.
        sort_by = list(self.instance.phase.transitions.keys())
        choices.sort(key=lambda k: sort_by.index(k[0]))
        action_field = self.fields['action']
        action_field.choices = choices
        self.should_show = bool(choices)


class BatchProgressSubmissionForm(forms.Form):
    action = forms.ChoiceField(label=_('Take action'))
    submissions = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'js-submissions-id'}))

    def __init__(self, *args, round=None, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        workflow = round and round.workflow
        self.action_mapping = get_action_mapping(workflow)
        choices = [(action, detail['display']) for action, detail in self.action_mapping.items()]
        self.fields['action'].choices = choices

    def clean_submissions(self):
        value = self.cleaned_data['submissions']
        submission_ids = [int(submission) for submission in value.split(',')]
        return ApplicationSubmission.objects.filter(id__in=submission_ids)

    def clean_action(self):
        value = self.cleaned_data['action']
        action = self.action_mapping[value]['transitions']
        return action


class ScreeningSubmissionForm(ApplicationSubmissionModelForm):

    class Meta:
        model = ApplicationSubmission
        fields = ('screening_statuses',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.has_default_screening_status_set:
            screening_status = instance.screening_statuses.get(default=True)
            self.fields['screening_statuses'].queryset = ScreeningStatus.objects.filter(
                yes=screening_status.yes
            )
        self.should_show = False
        if self.user.is_apply_staff:
            self.should_show = True

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance
        default_status = instance.screening_statuses.get(default=True)
        if default_status not in cleaned_data['screening_statuses']:
            self.add_error('screening_statuses', 'Can\'t remove default screening status.')
        return cleaned_data


class UpdateSubmissionLeadForm(ApplicationSubmissionModelForm):

    class Meta:
        model = ApplicationSubmission
        fields = ('lead',)

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        lead_field = self.fields['lead']
        lead_field.label = _('Update lead from {lead} to').format(lead=self.instance.lead)
        lead_field.queryset = lead_field.queryset.exclude(id=self.instance.lead.id)


class BatchUpdateSubmissionLeadForm(forms.Form):
    lead = forms.ChoiceField(label=_('Lead'))
    submissions = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'js-submissions-id'}))

    def __init__(self, *args, round=None, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['lead'].choices = [(staff.id, staff) for staff in User.objects.staff()]

    def clean_lead(self):
        value = self.cleaned_data['lead']
        return User.objects.get(id=value)

    def clean_submissions(self):
        value = self.cleaned_data['submissions']
        submission_ids = [int(submission) for submission in value.split(',')]
        return ApplicationSubmission.objects.filter(id__in=submission_ids)

    def save(self):
        new_lead = self.cleaned_data['lead']
        submissions = self.cleaned_data['submissions']

        for submission in submissions:
            # Onle save if the lead has changed.
            if submission.lead != new_lead:
                submission.lead = new_lead
                submission.save()

        return None


class BatchDeleteSubmissionForm(forms.Form):
    submissions = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'js-submissions-id'}))

    def __init__(self, *args, round=None, **kwargs):
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

    def clean_submissions(self):
        value = self.cleaned_data['submissions']
        submission_ids = [int(submission) for submission in value.split(',')]
        return ApplicationSubmission.objects.filter(id__in=submission_ids)

    def save(self):
        submissions = self.cleaned_data['submissions']
        submissions.delete()
        return None


class UpdateReviewersForm(ApplicationSubmissionModelForm):
    reviewer_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.reviewers().only('pk', 'full_name'),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Reviewers'}),
        label=_('Reviewers'),
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

        self.role_fields = {}
        field_data = make_role_reviewer_fields()

        for data in field_data:
            field_name = data['field_name']
            self.fields[field_name] = data['field']
            self.role_fields[field_name] = data['role']
            self.fields[field_name].initial = assigned_roles.get(data['role'])

        self.submitted_reviewers = User.objects.filter(
            id__in=self.instance.assigned.reviewed().values('reviewer'),
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
            if field in self.role_fields
        ]

        for field, role in self.role_fields.items():
            assigned_reviewer = AssignedReviewers.objects.filter(role=role, submission=self.instance).last()
            if assigned_reviewer and not cleaned_data[field] and assigned_reviewer.reviewer in self.submitted_reviewers:
                self.add_error(field, _("Can't unassign, just change, because review already submitted"))
                break

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
        """

        # 1. Update role reviewers
        assigned_roles = {
            role: self.cleaned_data[field]
            for field, role in self.role_fields.items()
        }
        for role, reviewer in assigned_roles.items():
            if reviewer:
                AssignedReviewers.objects.update_role(role, reviewer, instance)
            else:
                AssignedReviewers.objects.filter(role=role, submission=instance, review__isnull=True).delete()

        # 2. Update non-role reviewers
        # 2a. Remove those not on form
        if self.can_alter_external_reviewers(self.instance, self.user):
            reviewers = self.cleaned_data.get('reviewer_reviewers')
            assigned_reviewers = instance.assigned.without_roles()
            assigned_reviewers.never_tried_to_review().exclude(
                reviewer__in=reviewers
            ).delete()

            remaining_reviewers = assigned_reviewers.values_list('reviewer_id', flat=True)

            # 2b. Add in any new non-role reviewers selected
            AssignedReviewers.objects.bulk_create_reviewers(
                [reviewer for reviewer in reviewers if reviewer.id not in remaining_reviewers],
                instance,
            )

        return instance


class BatchUpdateReviewersForm(forms.Form):
    submissions = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'js-submissions-id'}))

    def __init__(self, *args, user=None, round=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.role_fields = {}
        field_data = make_role_reviewer_fields()

        for data in field_data:
            field_name = data['field_name']
            self.fields[field_name] = data['field']
            self.role_fields[field_name] = data['role']

    def clean_submissions(self):
        value = self.cleaned_data['submissions']
        submission_ids = [int(submission) for submission in value.split(',')]
        return ApplicationSubmission.objects.filter(id__in=submission_ids)

    def clean(self):
        cleaned_data = super().clean()
        role_reviewers = [
            user
            for field, user in self.cleaned_data.items()
            if field in self.role_fields
        ]

        # If any of the users match and are set to multiple roles, throw an error
        if len(role_reviewers) != len(set(role_reviewers)) and any(role_reviewers):
            self.add_error(None, _('Users cannot be assigned to multiple roles.'))

        return cleaned_data

    def save(self):
        submissions = self.cleaned_data['submissions']
        assigned_roles = {
            role: self.cleaned_data[field]
            for field, role in self.role_fields.items()
        }
        for role, reviewer in assigned_roles.items():
            if reviewer:
                AssignedReviewers.objects.update_role(role, reviewer, *submissions)

        return None


def make_role_reviewer_fields():
    role_fields = []
    staff_reviewers = User.objects.staff().only('full_name', 'pk')

    for role in ReviewerRole.objects.all().order_by('order'):
        role_name = bleach.clean(role.name, strip=True)
        field_name = 'role_reviewer_' + slugify(role_name)
        field = forms.ModelChoiceField(
            queryset=staff_reviewers,
            empty_label=_('-- No reviewer selected --'),
            required=False,
            label=mark_safe(render_icon(role.icon) + _('{role_name} Reviewer').format(role_name=role_name)),
        )
        role_fields.append({
            'role': role,
            'field': field,
            'field_name': field_name,
        })

    return role_fields


class UpdatePartnersForm(ApplicationSubmissionModelForm):
    partner_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.partners(),
        widget=Select2MultiCheckboxesWidget(attrs={'data-placeholder': 'Partners'}),
        label=_('Partners'),
        required=False,
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        partners = self.instance.partners.all()
        self.submitted_partners = User.objects.partners().filter(id__in=self.instance.reviews.values('author'))

        partner_field = self.fields['partner_reviewers']
        partner_field.queryset = partner_field.queryset.exclude(id__in=self.submitted_partners)
        partner_field.initial = partners

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        instance.partners.set(
            self.cleaned_data['partner_reviewers'] |
            self.submitted_partners
        )
        return instance


class GroupedModelChoiceIterator(forms.models.ModelChoiceIterator):
    def __init__(self, field, groupby):
        self.groupby = groupby
        super().__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset
        # Can't use iterator() when queryset uses prefetch_related()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, objs in groupby(queryset, self.groupby):
            yield (group, [self.choice(obj) for obj in objs])


class GroupedModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, *args, choices_groupby, **kwargs):
        if isinstance(choices_groupby, str):
            choices_groupby = methodcaller(choices_groupby)
        elif not callable(choices_groupby):
            raise TypeError('choices_groupby must either be a str or a callable accepting a single argument')
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return {'label': super().label_from_instance(obj), 'disabled': not obj.is_leaf()}


class UpdateMetaTermsForm(ApplicationSubmissionModelForm):
    meta_terms = GroupedModelMultipleChoiceField(
        queryset=None,  # updated in init method
        widget=MetaTermSelect2Widget(attrs={'data-placeholder': 'Meta terms'}),
        label=_('Meta terms'),
        choices_groupby='get_parent',
        required=False,
        help_text=_('Meta terms are hierarchical in nature.'),
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['meta_terms'].queryset = MetaTerm.get_root_descendants().exclude(depth=2)


class CreateReminderForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(),
        widget=forms.HiddenInput(),
    )
    time = forms.DateField()

    def __init__(self, instance=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if instance:
            self.fields['submission'].initial = instance.id

    def save(self, *args, **kwargs):
        return Reminder.objects.create(
            title=self.cleaned_data['title'],
            description=self.cleaned_data['description'],
            time=self.cleaned_data['time'],
            submission=self.cleaned_data['submission'],
            user=self.user)

    class Meta:
        model = Reminder
        fields = ['title', 'description', 'time', 'action']
