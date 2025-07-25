from django import forms
from django.db import transaction
from django.utils import timezone

from hypha.apply.review.forms import MixedMetaClass
from hypha.apply.stream_forms.forms import StreamBaseForm

from .models import Report, ReportConfig, ReportVersion


class ReportEditForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    class Meta:
        model = Report
        fields: list = []

    def __init__(self, *args, user=None, initial=None, **kwargs):
        if initial is None:
            initial = {}
        # Need to populate form_fields, right?
        # No: The form_fields got populated from the view which instantiated this Form.
        # Yes: they don't seem to be here.
        # No: this is not where the magic happens.
        # self.form_fields = kwargs.pop("form_fields", {})
        # Need to populate form_data, right? Yes. No. IDK. Appears no.
        # self.form_data = kwargs.pop("form_data", {})
        # OK, both yes and no. If there is an existing value it will come via "initial", so if present there, use them.
        # if initial["form_fields"] is not None:
        #     self.form_fields = initial["form_fields"]
        # if initial["form_data"] is not None:
        #     self.form_data = initial["form_data"]
        # But this should not be needed because super().__init__ will already take these initial values and use them.
        super().__init__(*args, initial=initial, **kwargs)
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["form_data"] = {
            key: value
            for key, value in cleaned_data.items()
            if key not in self._meta.fields
        }
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True, form_fields=dict):
        self.instance.form_fields = form_fields
        instance = super().save(commit)
        # We need to save the fields first, not attempt to save form_data on first save, then update the form_data next.
        # Otherwise, we don't get access to the generator method "question_field_ids" which we use to prevent temp file
        # fields from getting into the saved form_data.
        # Inspired by ProjectForm.save and ProjectSOWForm.save but enhanced to support multi-answer fields.
        instance.form_data = {
            field: self.cleaned_data["form_data"][field]
            for field in self.cleaned_data["form_data"]
            # Where do we get question_field_ids? On the version, but only when it exists, thus the create-then-update.
            # The split-on-underscore supports the use of multi-answer fields such as MultiInputCharFieldBlock.
            if field.split("_")[0] in instance.question_field_ids
        }
        # In case there are stream form file fields, process those here.
        instance.process_file_data(
            self.cleaned_data["form_data"],
            latest_existing_data=instance.current.form_data
            if instance.current
            else None,
        )

        is_draft = "save" in self.data
        version = ReportVersion.objects.create(
            report=instance,
            # Save a ReportVersion first then edit/update the form_data below.
            form_data=instance.form_data,
            submitted=timezone.now(),
            draft=is_draft,
            author=self.user,
        )
        version.process_file_data(
            self.cleaned_data["form_data"],
            latest_existing_data=instance.current.form_data
            if instance.current
            else None,
        )
        version.save()

        if is_draft:
            instance.draft = version
        else:
            # If this is the first submission of the report we track that as the
            # submitted date of the report
            if not instance.submitted:
                instance.author = self.user
                instance.submitted = version.submitted
            instance.current = version
            instance.draft = None
        instance.save()
        return instance


class ReportFrequencyForm(forms.ModelForm):
    start = forms.DateField(label="Report on:", required=False)

    class Meta:
        model = ReportConfig
        fields = ("start", "occurrence", "frequency", "does_not_repeat")
        labels = {
            "occurrence": "",
            "frequency": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurrence"].required = False
        self.fields["frequency"].required = False
