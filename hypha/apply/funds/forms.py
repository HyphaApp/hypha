from collections import OrderedDict
from functools import partial
from itertools import groupby
from operator import methodcaller

import nh3
from django import forms
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail.signal_handlers import disable_reference_index_auto_update

from hypha.apply.categories.models import MetaTerm
from hypha.apply.users.models import User

from .models import (
    ApplicationSubmission,
    AssignedReviewers,
    CoApplicant,
    CoApplicantInvite,
    Reminder,
    ReviewerRole,
)
from .models.co_applicants import CoApplicantProjectPermission, CoApplicantRole
from .permissions import can_change_external_reviewers
from .utils import model_form_initial, render_icon
from .widgets import MetaTermWidget, MultiCheckboxesWidget


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
                "The %s could not be %s because the data didn't validate."
                % (
                    self.instance._meta.object_name,
                    "created" if self.instance._state.adding else "changed",
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
    action = forms.ChoiceField(label=_("Take action"))

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        choices = list(self.instance.get_actions_for_user(self.user))
        # Sort the transitions by the order they are listed.
        sort_by = list(self.instance.phase.transitions.keys())
        choices.sort(key=lambda k: sort_by.index(k[0]))
        action_field = self.fields["action"]
        action_field.choices = choices


class UpdateSubmissionLeadForm(ApplicationSubmissionModelForm):
    class Meta:
        model = ApplicationSubmission
        fields = ("lead",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lead_field = self.fields["lead"]
        lead_field.label = _("Update lead from {lead} to").format(
            lead=self.instance.lead
        )
        lead_field.queryset = lead_field.queryset.exclude(id=self.instance.lead.id)
        lead_field.widget.attrs.update({"data-js-choices": ""})


class UpdateReviewersForm(ApplicationSubmissionModelForm):
    reviewer_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.reviewers().only("pk", "full_name"),
        label=_("External Reviewers"),
        required=False,
    )
    reviewer_reviewers.widget.attrs.update(
        {"data-placeholder": _("Select..."), "data-js-choices": ""}
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        if kwargs.get("instance"):
            # Providing initials(from model's instance) to BaseModelForm
            kwargs["initial"] = model_form_initial(
                kwargs.get("instance"), self._meta.fields, self._meta.exclude
            )
        super().__init__(*args, **kwargs)

        # convert a python dict to orderedDict, to use move_to_end method
        self.fields = OrderedDict(self.fields)

        assigned_roles = {
            assigned.role: assigned.reviewer
            for assigned in self.instance.assigned.filter(role__isnull=False)
        }

        self.role_fields = {}
        field_data = make_role_reviewer_fields()

        for data in field_data:
            field_name = data["field_name"]
            self.fields[field_name] = data["field"]
            self.role_fields[field_name] = data["role"]
            self.fields[field_name].initial = assigned_roles.get(data["role"])
            self.fields[field_name].widget.attrs.update({"data-js-choices": ""})

        self.submitted_reviewers = User.objects.filter(
            id__in=self.instance.assigned.reviewed().values("reviewer"),
        )

        if can_change_external_reviewers(user=self.user, submission=self.instance):
            reviewers = self.instance.reviewers.all().only("pk")
            self.prepare_field(
                "reviewer_reviewers",
                initial=reviewers,
                excluded=self.submitted_reviewers,
            )

            # Move the non-role reviewers field to the end of the field list
            self.fields.move_to_end("reviewer_reviewers")
        else:
            self.fields.pop("reviewer_reviewers")

    def prepare_field(self, field_name, initial, excluded):
        field = self.fields[field_name]
        field.queryset = field.queryset.exclude(id__in=excluded)
        field.initial = initial

    def clean(self):
        cleaned_data = super().clean()
        role_reviewers = [
            user
            for field, user in self.cleaned_data.items()
            if field in self.role_fields and user
        ]

        for field, role in self.role_fields.items():
            assigned_reviewer = AssignedReviewers.objects.filter(
                role=role, submission=self.instance
            ).last()
            if (
                assigned_reviewer
                and (not cleaned_data[field] and assigned_reviewer.reviewer.is_active)
                and assigned_reviewer.reviewer in self.submitted_reviewers
            ):
                self.add_error(
                    field,
                    _("Can't unassign, just change, because review already submitted"),
                )
                break

        # If any of the users match and are set to multiple roles, throw an error
        if len(role_reviewers) != len(set(role_reviewers)) and any(role_reviewers):
            self.add_error(None, _("Users cannot be assigned to multiple roles."))

        return cleaned_data

    def save(self, *args, **kwargs):
        """
        1. Update role reviewers
        2. Update non-role reviewers
            2a. Remove those not on form
            2b. Add in any new non-role reviewers selected
        """
        with disable_reference_index_auto_update():
            instance = super().save(*args, **kwargs)

            # 1. Update role reviewers
            assigned_roles = {
                role: self.cleaned_data[field]
                for field, role in self.role_fields.items()
            }
            for role, reviewer in assigned_roles.items():
                if reviewer:
                    AssignedReviewers.objects.update_role(role, reviewer, instance)
                else:
                    AssignedReviewers.objects.filter(
                        role=role, submission=instance, review__isnull=True
                    ).delete()

            # 2. Update non-role reviewers
            # 2a. Remove those not on form
            if can_change_external_reviewers(submission=self.instance, user=self.user):
                reviewers = self.cleaned_data.get("reviewer_reviewers")
                assigned_reviewers = instance.assigned.without_roles()
                assigned_reviewers.never_tried_to_review().exclude(
                    reviewer__in=reviewers
                ).delete()

                remaining_reviewers = assigned_reviewers.values_list(
                    "reviewer_id", flat=True
                )

                # 2b. Add in any new non-role reviewers selected
                AssignedReviewers.objects.bulk_create_reviewers(
                    [
                        reviewer
                        for reviewer in reviewers
                        if reviewer.id not in remaining_reviewers
                    ],
                    instance,
                )

            return instance


class BatchUpdateReviewersForm(forms.Form):
    submissions = forms.CharField(
        widget=forms.HiddenInput(attrs={"class": "js-submissions-id"})
    )
    external_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.reviewers().only("pk", "full_name"),
        widget=MultiCheckboxesWidget(attrs={"data-placeholder": _("Select...")}),
        label=_("External Reviewers"),
        required=False,
    )

    def __init__(self, *args, user=None, round=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = kwargs.pop("request", None)
        self.user = user
        self.fields = OrderedDict(self.fields)

        self.role_fields = {}
        field_data = make_role_reviewer_fields()

        for data in field_data:
            field_name = data["field_name"]
            self.fields[field_name] = data["field"]
            self.role_fields[field_name] = data["role"]
            self.fields[field_name].widget.attrs.update({"data-js-choices": ""})

        self.fields.move_to_end("external_reviewers")

    def clean_submissions(self):
        value = self.cleaned_data["submissions"]
        submission_ids = [int(submission) for submission in value.split(",")]
        return ApplicationSubmission.objects.filter(id__in=submission_ids)

    def clean(self):
        cleaned_data = super().clean()
        external_reviewers = self.cleaned_data["external_reviewers"]
        submissions = self.cleaned_data["submissions"]
        if external_reviewers:
            # User needs to be superuser or lead of all selected submissions.

            if not all(
                can_change_external_reviewers(submission=s, user=self.user)
                for s in submissions
            ):
                self.add_error(
                    "external_reviewers",
                    _(
                        "Make sure all submissions support external reviewers and you are lead for all the selected submissions."
                    ),
                )

        role_reviewers = [
            user
            for field, user in self.cleaned_data.items()
            if field in self.role_fields and user
        ]

        # If any of the users match and are set to multiple roles, throw an error
        if len(role_reviewers) != len(set(role_reviewers)) and any(role_reviewers):
            self.add_error(None, _("Users cannot be assigned to multiple roles."))

        return cleaned_data

    def submissions_cant_have_external_reviewers(self, submissions):
        for submission in submissions:
            if not submission.stage.has_external_review:
                return True
        return False


def make_role_reviewer_fields():
    role_fields = []
    staff_reviewers = User.objects.staff().only("full_name", "pk")

    for role in ReviewerRole.objects.all().order_by("order"):
        role_name = nh3.clean(role.name, tags=set())
        field_name = f"role_reviewer_{role.id}"
        field = forms.ModelChoiceField(
            queryset=staff_reviewers,
            empty_label=_("---"),
            required=False,
            label=mark_safe(
                render_icon(role.icon)
                + _("{role_name} Reviewer").format(role_name=role_name)
            ),
        )
        role_fields.append(
            {
                "role": role,
                "field": field,
                "field_name": field_name,
            }
        )

    return role_fields


class UpdatePartnersForm(ApplicationSubmissionModelForm):
    partner_reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.partners(),
        label=_("Partners"),
        required=False,
    )
    partner_reviewers.widget.attrs.update(
        {"data-placeholder": _("Select..."), "data-js-choices": ""}
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        kwargs.pop("user")
        super().__init__(*args, **kwargs)
        partners = self.instance.partners.all()
        self.submitted_partners = User.objects.partners().filter(
            id__in=self.instance.reviews.values("author")
        )

        partner_field = self.fields["partner_reviewers"]

        # If applicant is also a partner, they should not be allowed to be a partner on their own application
        partner_field.queryset = partner_field.queryset.exclude(
            Q(id__in=self.submitted_partners) | Q(id=self.instance.user.id)
        )
        partner_field.initial = partners

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)

        instance.partners.set(
            self.cleaned_data["partner_reviewers"] | self.submitted_partners
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
            raise TypeError(
                "choices_groupby must either be a str or a callable accepting a single argument"
            )
        self.iterator = partial(GroupedModelChoiceIterator, groupby=choices_groupby)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        return {
            "label": super().label_from_instance(obj),
            "disabled": not obj.is_leaf(),
        }


class UpdateMetaTermsForm(ApplicationSubmissionModelForm):
    meta_terms = GroupedModelMultipleChoiceField(
        queryset=None,  # updated in init method
        widget=MetaTermWidget(
            attrs={"data-placeholder": "Select...", "data-js-choices": ""}
        ),
        label=_("Tags"),
        choices_groupby="get_parent",
        required=False,
        help_text=_("Tags are hierarchical in nature."),
    )

    class Meta:
        model = ApplicationSubmission
        fields: list = []

    def __init__(self, *args, **kwargs):
        kwargs.pop("user")
        super().__init__(*args, **kwargs)
        self.fields["meta_terms"].queryset = MetaTerm.get_root_descendants().exclude(
            depth=2
        )
        # Set initial values for meta_terms based on the instance if available
        if self.instance.pk:
            self.fields["meta_terms"].initial = self.instance.meta_terms.values_list(
                "id", flat=True
            )


class CreateReminderForm(forms.ModelForm):
    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(),
        widget=forms.HiddenInput(),
    )
    time = forms.DateField()

    def __init__(self, *args, instance=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if instance:
            self.fields["submission"].initial = instance.id

    def save(self, *args, **kwargs):
        return Reminder.objects.create(
            title=self.cleaned_data["title"],
            description=self.cleaned_data["description"],
            time=self.cleaned_data["time"],
            submission=self.cleaned_data["submission"],
            user=self.user,
        )

    class Meta:
        model = Reminder
        fields = ["title", "description", "time", "action"]


class InviteCoApplicantForm(forms.ModelForm):
    invited_user_email = forms.EmailField(required=True, label="Email")
    role = forms.ChoiceField(
        choices=CoApplicantRole.choices, label="Role", required=False
    )
    project_permission = forms.MultipleChoiceField(
        choices=CoApplicantProjectPermission.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Project permissions"),
        help_text=_(
            "Enable same access level to these sections. Example: View role + Contracting = read-only contracting access."
        ),
    )

    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(),
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, submission, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invited_by = user

        if submission:
            self.fields["submission"].initial = submission.id
            if not hasattr(submission, "project"):
                self.fields.pop("project_permission", None)

    class Meta:
        model = CoApplicantInvite
        fields = ["invited_user_email", "submission"]


class EditCoApplicantForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=CoApplicantRole.choices, label="Role", required=False
    )
    project_permission = forms.MultipleChoiceField(
        choices=CoApplicantProjectPermission.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label=_("Project permissions"),
        help_text=_(
            "Enable same access level to these sections. Example: View role + Contracting = read-only contracting access."
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if not hasattr(instance.submission, "project"):
            self.fields.pop("project_permission", None)

    class Meta:
        model = CoApplicant
        fields = ("role", "project_permission")
