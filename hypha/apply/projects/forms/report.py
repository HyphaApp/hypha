from django import forms
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.stream_forms.fields import MultiFileField
from hypha.apply.utils.fields import RichTextField

from ..models.report import Report, ReportConfig, ReportPrivateFiles, ReportVersion


class ReportEditForm(FileFormMixin, forms.ModelForm):
    public_content = RichTextField(
        help_text=_(
            "This section of the report will be shared with the broader community."
        )
    )
    private_content = RichTextField(
        help_text=_("This section of the report will be shared with staff only.")
    )
    file_list = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={"class": "delete"}),
        queryset=ReportPrivateFiles.objects.all(),
        required=False,
        label=_("Files"),
    )
    files = MultiFileField(required=False, label="")

    class Meta:
        model = Report
        fields = (
            "public_content",
            "private_content",
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
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        public = cleaned_data["public_content"]
        private = cleaned_data["private_content"]
        if not private and not public:
            missing_content = _(
                "Must include either public or private content when submitting a report."
            )
            self.add_error("public_content", missing_content)
            self.add_error("private_content", missing_content)
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        is_draft = "save" in self.data

        version = ReportVersion.objects.create(
            report=self.instance,
            public_content=self.cleaned_data["public_content"],
            private_content=self.cleaned_data["private_content"],
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
