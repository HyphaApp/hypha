from django import forms
from django.db import transaction
from django.utils import timezone

from wagtail.fields import StreamField

from hypha.apply.stream_forms.fields import MultiFileField
from ..blocks import ProjectApprovalFormCustomFormFieldsBlock
from ..models import ProjectReportForm

from ..models.report import Report, ReportConfig, ReportPrivateFiles, ReportVersion
from ...funds.models.forms import ApplicationBaseProjectReportForm
from ...review.forms import MixedMetaClass
from ...stream_forms.files import StreamFieldDataEncoder
from ...stream_forms.forms import StreamBaseForm


class ReportEditForm(StreamBaseForm, forms.ModelForm, metaclass=MixedMetaClass):
    # The fields need to be populated from the associated fund form. Should that happen in init?
    form_fields = StreamField(
        ProjectApprovalFormCustomFormFieldsBlock(),
        use_json_field=True,
        # TODO: this will not be "first()" but one selected by submission id via ApplicationBaseProjectReportForm
        default=ProjectReportForm.objects.first(),
    )
    form_data = forms.JSONField(encoder=StreamFieldDataEncoder)
    file_list = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "delete"}),
        queryset=ReportPrivateFiles.objects.all(),
        required=False,
        label="Files",
    )
    files = MultiFileField(required=False, label="")

    class Meta:
        model = Report
        fields = (
            "file_list",
            "files",
        )

    def __init__(self, *args, user=None, initial=None, **kwargs):
        if initial is None:
            initial = {}
        self.report_files = initial.pop(
            "file_list",
            ReportPrivateFiles.objects.none(),
        )
        super().__init__(*args, initial=initial, **kwargs)
        self.fields["file_list"].queryset = self.report_files
        # Need to populate form_fields, right?
        # ApplicationBaseProjectReportForm is where the link between the ProjectReportForm and Submission lives.
        #self.fields["form_fields"].queryset = queryset=ApplicationBaseProjectReportForm.objects.all() #.filter(
        #application=self.instance.project.submission.round.id
        #).first().form.form_fields
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
    def save(self, commit=True):
        is_draft = "save" in self.data

        version = ReportVersion.objects.create(
            report=self.instance,
            form_fields=self.form_fields,
            form_data=self.cleaned_data["form_data"],
            submitted=timezone.now(),
            draft=is_draft,
            author=self.user,
        )

        if is_draft:
            self.instance.draft = version
        else:
            # If this is the first submission of the report we track that as the
            # submitted date of the report
            if not self.instance.submitted:
                self.instance.submitted = version.submitted
            self.instance.current = version
            self.instance.draft = None

        instance = super().save(commit)

        removed_files = self.cleaned_data["file_list"]
        ReportPrivateFiles.objects.bulk_create(
            ReportPrivateFiles(report=version, document=file.document)
            for file in self.report_files
            if file not in removed_files
        )

        added_files = self.cleaned_data["files"]
        if added_files:
            ReportPrivateFiles.objects.bulk_create(
                ReportPrivateFiles(report=version, document=file)
                for file in added_files
            )

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
