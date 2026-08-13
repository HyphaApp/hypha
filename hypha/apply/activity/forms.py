from django import forms
from django.db import transaction
from django.forms.widgets import Textarea
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.stream_forms.fields import MultiFileField
from hypha.apply.todo.options import COMMENT_TASK
from hypha.apply.todo.views import add_task_to_user
from hypha.apply.users.models import STAFF_GROUP_NAME, User
from hypha.core.widgets import PagedownWidget

from .models import Activity, ActivityAttachment


class CommentForm(FileFormMixin, forms.ModelForm):
    attachments = MultiFileField(label=_("Attachments"), required=False)
    assign_to = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name=STAFF_GROUP_NAME),
        required=False,
        empty_label=_("Select..."),
        label=_("Assign to"),
    )
    assign_to.widget.attrs.update({"data-js-choices": ""})

    class Meta:
        model = Activity

        # Fields that should only be included when the mini comment form is used
        # as the mini form can be put anywhere and associated to any object.
        mini_fields = (
            "related_content_type",
            "related_object_id",
            "source_content_type",
            "source_object_id",
        )
        fields = ("message", "visibility", "assign_to", *mini_fields)
        labels = {
            "visibility": _("Visible to"),
            "message": _("Message"),
        }
        help_texts = {
            "visibility": _(
                "Select a relevant user role. Staff can view every comment."
            )
        }
        widgets = {
            "visibility": forms.RadioSelect(),
            "message": PagedownWidget(),
            **{field: forms.HiddenInput() for field in mini_fields},
        }

    def __init__(self, *args, user=None, has_coapplicants=False, mini=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.visibility_choices = self._meta.model.visibility_choices_for(
            user, has_coapplicants
        )
        visibility = self.fields["visibility"]
        # Set default visibility to "Applicant" for staff and staff can view everything.
        visibility.initial = self.visibility_choices[0]
        if len(self.visibility_choices) > 1:
            visibility.choices = self.visibility_choices
        else:
            visibility.required = False
            visibility.choices = self.visibility_choices
            visibility.initial = visibility.initial[0]
            visibility.widget = forms.HiddenInput()
        if not user.is_apply_staff:
            self.fields["assign_to"].widget = forms.HiddenInput()

        if mini:
            self.fields["message"].widget = Textarea(
                attrs={"rows": 2, "placeholder": "Write a comment..."}
            )
        else:
            # If not mini, remove the unneeded fields from the form.
            for key in self.Meta.mini_fields:
                del self.fields[key]

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=True)
        added_files = self.cleaned_data["attachments"]
        assigned_user = self.cleaned_data["assign_to"]
        if assigned_user:
            # add task to assigned user
            add_task_to_user(
                code=COMMENT_TASK,
                user=assigned_user,
                related_obj=instance,
            )
        if added_files:
            ActivityAttachment.objects.bulk_create(
                ActivityAttachment(activity=instance, file=file) for file in added_files
            )
        return instance
