from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.stream_forms.fields import SingleFileField
from hypha.apply.stream_forms.forms import StreamBaseForm
from hypha.apply.users.groups import STAFF_GROUP_NAME

from ..models.project import (
    CLOSING,
    COMPLETE,
    DRAFT,
    INVOICING_AND_REPORTING,
    PAF_STATUS_CHOICES,
    PROJECT_STATUS_CHOICES,
    Contract,
    ContractPacketFile,
    PacketFile,
    PAFApprovals,
    PAFReviewersRole,
    Project,
    ProjectSOW,
)

User = get_user_model()


def filter_request_choices(choices):
    return [(k, v) for k, v in PROJECT_STATUS_CHOICES if k in choices]


def get_latest_project_paf_approval_via_roles(project, roles):
    # exact match the roles with paf approval's reviewer roles
    paf_approvals = project.paf_approvals.annotate(
        roles_count=Count("paf_reviewer_role__user_roles")
    ).filter(roles_count=len(list(roles)), approved=False)

    for role in roles:
        paf_approvals = paf_approvals.filter(paf_reviewer_role__user_roles__id=role.id)
    return paf_approvals.first()


class ApproveContractForm(forms.Form):
    id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, instance, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            self.fields["id"].initial = instance.id

    def clean_id(self):
        if self.has_changed():
            raise forms.ValidationError(
                _("Something changed before your approval please re-review")
            )

    def clean(self):
        if not self.instance:
            raise forms.ValidationError(
                _("The contract you were trying to approve has already been approved")
            )

        if not self.instance.signed_by_applicant:
            raise forms.ValidationError(_("You can only approve a signed contract"))

        super().clean()

    def save(self, *args, **kwargs):
        self.instance.save()
        return self.instance


class CreateProjectForm(forms.Form):
    submission = forms.ModelChoiceField(
        queryset=ApplicationSubmission.objects.filter(project__isnull=True),
        widget=forms.HiddenInput(),
    )

    project_lead = forms.ModelChoiceField(
        label=_("Select Project Lead"), queryset=User.objects.all()
    )

    def __init__(self, instance=None, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if instance:
            self.fields["submission"].initial = instance.id

        # Update lead field queryset
        lead_field = self.fields["project_lead"]
        qwargs = Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        lead_field.queryset = lead_field.queryset.filter(qwargs).distinct()
        if instance:
            lead_field.initial = instance.lead

    def clean_project_lead(self):
        project_lead = self.cleaned_data["project_lead"]
        if not project_lead:
            raise forms.ValidationError(_("Project lead is a required field"))
        return project_lead

    def save(self, *args, **kwargs):
        submission = self.cleaned_data["submission"]
        lead = self.cleaned_data["project_lead"]
        return Project.create_from_submission(submission, lead=lead)


class MixedMetaClass(type(StreamBaseForm), type(forms.ModelForm)):
    pass


class ProjectApprovalForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    class Meta:
        fields = [
            "title",
        ]
        model = Project
        widgets = {"title": forms.HiddenInput()}

    def __init__(self, *args, extra_fields=None, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["form_data"] = {
            key: value
            for key, value in cleaned_data.items()
            if key not in self._meta.fields
        }
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.form_fields = kwargs.pop("paf_form_fields", {})
        self.instance.form_data = {
            field: self.cleaned_data[field]
            for field in self.instance.question_field_ids
            if field in self.cleaned_data
        }
        self.instance.process_file_data(self.cleaned_data)
        self.instance.user_has_updated_details = True
        return super().save(*args, **kwargs)


class ProjectSOWForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    class Meta:
        fields = [
            "project",
        ]
        model = ProjectSOW
        widgets = {"project": forms.HiddenInput()}

    def __init__(self, *args, extra_fields=None, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["form_data"] = {
            key: value
            for key, value in cleaned_data.items()
            if key not in self._meta.fields
        }
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance, _ = self._meta.model.objects.get_or_create(
            project=kwargs.pop("project", None)
        )
        self.instance.form_fields = kwargs.pop("sow_form_fields", {})
        self.instance.form_data = {
            field: self.cleaned_data[field]
            for field in self.instance.question_field_ids
            if field in self.cleaned_data
        }
        self.instance.process_file_data(self.cleaned_data)
        return super().save(*args, **kwargs)


class ChangePAFStatusForm(forms.ModelForm):
    name_prefix = "change_paf_status_form"
    paf_status = forms.ChoiceField(
        label=_("PAF status"), choices=PAF_STATUS_CHOICES, widget=forms.RadioSelect()
    )
    comment = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        fields = ["paf_status", "comment"]
        model = Project

    def __init__(self, instance, user, *args, **kwargs):
        super().__init__(*args, **kwargs, instance=instance)
        self.fields["paf_status"].widget.attrs["class"] = "grid--status-update"


class ChangeProjectStatusForm(forms.ModelForm):
    name_prefix = "change_project_status_form"
    comment = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        fields = ["status", "comment"]
        model = Project

    def __init__(self, instance, user, *args, **kwargs):
        super().__init__(*args, **kwargs, instance=instance)
        status_field = self.fields["status"]
        possible_status_transitions = {
            INVOICING_AND_REPORTING: filter_request_choices([CLOSING, COMPLETE]),
            CLOSING: filter_request_choices([INVOICING_AND_REPORTING, COMPLETE]),
            COMPLETE: filter_request_choices([INVOICING_AND_REPORTING, CLOSING]),
        }
        status_field.choices = possible_status_transitions.get(instance.status, [])


class RemoveDocumentForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        fields = ["id"]
        model = PacketFile

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RemoveContractDocumentForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        fields = ["id"]
        model = ContractPacketFile

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ApproversForm(forms.ModelForm):
    class Meta:
        fields = ["id"]
        model = Project
        widgets = {"id": forms.HiddenInput()}

    def __init__(self, user=None, *args, **kwargs):
        from hypha.apply.activity.adapters.utils import get_users_for_groups

        super().__init__(*args, **kwargs)

        for paf_reviewer_role in PAFReviewersRole.objects.all():
            users = get_users_for_groups(
                list(paf_reviewer_role.user_roles.all()), exact_match=True
            )
            approval = PAFApprovals.objects.filter(
                project=self.instance, paf_reviewer_role=paf_reviewer_role
            )
            if approval:
                initial_user = approval.first().user
            self.fields[slugify(paf_reviewer_role.label)] = forms.ModelChoiceField(
                queryset=users,
                required=False,
                blank=True,
                label=paf_reviewer_role.label,
                initial=initial_user if approval else None,
                disabled=approval.first().approved if approval.first() else False,
                # using approval.first() as condition for existing projects
            )

    def save(self, commit=True):
        # add users as PAFApprovals
        for paf_reviewer_role in PAFReviewersRole.objects.all():
            assigned_user = self.cleaned_data[slugify(paf_reviewer_role.label)]
            paf_approvals = PAFApprovals.objects.filter(
                project=self.instance, paf_reviewer_role=paf_reviewer_role
            )
            if not paf_approvals.exists():
                PAFApprovals.objects.create(
                    project=self.instance,
                    paf_reviewer_role=paf_reviewer_role,
                    user=assigned_user if assigned_user else None,
                    approved=False,
                )
            elif not paf_approvals.first().approved:
                paf_approval = paf_approvals.first()
                paf_approval.user = assigned_user if assigned_user else None
                paf_approval.save()
        return super().save(commit=True)


class SetPendingForm(ApproversForm):
    def clean(self):
        if self.instance.status != DRAFT:
            raise forms.ValidationError(
                _("A Project can only be sent for Approval when Drafted.")
            )

        # :todo: we should have a check form contains enough data to create PAF Approvals
        cleaned_data = super().clean()
        return cleaned_data


class AssignApproversForm(forms.ModelForm):
    class Meta:
        fields = ["id"]
        model = Project
        widgets = {"id": forms.HiddenInput()}

    def __init__(self, user=None, *args, **kwargs):
        from hypha.apply.activity.adapters.utils import get_users_for_groups

        super().__init__(*args, **kwargs)
        self.user = user

        paf_approval = get_latest_project_paf_approval_via_roles(
            project=self.instance, roles=user.groups.all()
        )

        if paf_approval:
            current_paf_reviewer_role = paf_approval.paf_reviewer_role

            users = get_users_for_groups(
                list(current_paf_reviewer_role.user_roles.all()), exact_match=True
            )

            self.fields[slugify(current_paf_reviewer_role.label)] = (
                forms.ModelChoiceField(
                    queryset=users,
                    required=False,
                    blank=True,
                    label=current_paf_reviewer_role.label,
                    initial=paf_approval.user,
                    disabled=paf_approval.approved,
                )
            )

    def save(self, commit=True):
        paf_approval = get_latest_project_paf_approval_via_roles(
            project=self.instance, roles=self.user.groups.all()
        )

        current_paf_reviewer_role = paf_approval.paf_reviewer_role
        assigned_user = self.cleaned_data[slugify(current_paf_reviewer_role.label)]

        if not paf_approval.approved:
            paf_approval.user = assigned_user if assigned_user else None
            paf_approval.save()

        return super().save(commit=True)


class SubmitContractDocumentsForm(forms.ModelForm):
    class Meta:
        fields = ["id"]
        model = Project
        widgets = {"id": forms.HiddenInput()}

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)


class UploadContractForm(FileFormMixin, forms.ModelForm):
    file = SingleFileField(label=_("Contract"), required=True)

    class Meta:
        fields = ["file"]
        model = Contract

    def save(self, commit=True):
        self.instance.file = self.cleaned_data.get("file")
        return super().save(commit=True)


class StaffUploadContractForm(FileFormMixin, forms.ModelForm):
    file = SingleFileField(label=_("Contract"), required=True)

    class Meta:
        fields = ["file", "signed_by_applicant"]
        model = Contract


class UploadDocumentForm(FileFormMixin, forms.ModelForm):
    document = SingleFileField(label=_("Document"), required=True)

    class Meta:
        fields = ["category", "document"]
        model = PacketFile

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.title = self.instance.document
        return super(UploadDocumentForm, self).save(commit=True)


class UploadContractDocumentForm(FileFormMixin, forms.ModelForm):
    document = SingleFileField(label=_("Contract Document"), required=True)

    class Meta:
        fields = ["category", "document"]
        model = ContractPacketFile

    def __init__(self, user=None, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        self.instance.title = self.instance.document
        return super(UploadContractDocumentForm, self).save(commit=True)


class UpdateProjectLeadForm(forms.ModelForm):
    class Meta:
        fields = ["lead"]
        model = Project

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lead_field = self.fields["lead"]
        lead_field.label = _("Update lead from {lead} to").format(
            lead=self.instance.lead
        )

        qwargs = Q(groups__name=STAFF_GROUP_NAME) | Q(is_superuser=True)
        lead_field.queryset = (
            lead_field.queryset.exclude(pk=self.instance.lead_id)
            .filter(qwargs)
            .distinct()
        )
