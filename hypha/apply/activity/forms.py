from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin
from pagedown.widgets import PagedownWidget

from hypha.apply.stream_forms.fields import MultiFileField
from hypha.apply.todo.options import COMMENT_TASK
from hypha.apply.todo.views import add_task_to_user
from hypha.apply.users.models import STAFF_GROUP_NAME, User

from .models import Activity, ActivityAttachment


class CommentForm(FileFormMixin, forms.ModelForm):
    attachments = MultiFileField(label=_("Attachments"), required=False)
    assign_to = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name=STAFF_GROUP_NAME),
        required=False,
        empty_label=_("Select..."),
        label=_("Assign to"),
    )

    class Meta:
        model = Activity
        fields = (
            "message",
            "visibility",
            "assign_to",
        )
        labels = {
            "visibility": "Visible to",
            "message": "Message",
        }
        help_texts = {
            "visibility": "Select a relevant user role. Staff can view every comment."
        }
        widgets = {
            "visibility": forms.RadioSelect(),
            "message": PagedownWidget(),
        }

    def __init__(self, *args, user=None, **kwargs):
        # Get `submission_partner_list` kwarg and remove it before initializing parent.
        submission_partner_list = None
        if "submission_partner_list" in kwargs:
            submission_partner_list = kwargs.pop("submission_partner_list")

        super().__init__(*args, **kwargs)
        self.visibility_choices = self._meta.model.visibility_choices_for(
            user, submission_partner_list
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
