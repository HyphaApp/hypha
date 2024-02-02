from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin
from pagedown.widgets import PagedownWidget

from hypha.apply.stream_forms.fields import MultiFileField

from .models import Activity, ActivityAttachment


class CommentForm(FileFormMixin, forms.ModelForm):
    attachments = MultiFileField(label=_("Attachments"), required=False)

    class Meta:
        model = Activity
        fields = ("message", "visibility")
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

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=True)
        added_files = self.cleaned_data["attachments"]
        if added_files:
            ActivityAttachment.objects.bulk_create(
                ActivityAttachment(activity=instance, file=file) for file in added_files
            )

        return instance
