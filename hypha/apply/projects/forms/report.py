from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_file_form.forms import FileFormMixin

from hypha.apply.stream_forms.fields import MultiFileField
from hypha.apply.utils.fields import RichTextField

from ..models.report import Report, ReportConfig, ReportPrivateFiles, ReportVersion


class ReportEditForm(FileFormMixin, forms.ModelForm):
    public_content = RichTextField(
        help_text="This section of the report will be shared with the broader community."
    )
    private_content = RichTextField(
        help_text="This section of the report will be shared with staff only."
    )
    file_list = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'delete'}),
        queryset=ReportPrivateFiles.objects.all(),
        required=False,
        label='Files'
    )
    files = MultiFileField(required=False, label='')

    class Meta:
        model = Report
        fields = (
            'public_content',
            'private_content',
            'file_list',
            'files',
        )

    def __init__(self, *args, user=None, initial={}, **kwargs):
        self.report_files = initial.pop(
            'file_list',
            ReportPrivateFiles.objects.none(),
        )
        super().__init__(*args, initial=initial, **kwargs)
        self.fields['file_list'].queryset = self.report_files
        self.user = user

    def clean(self):
        cleaned_data = super().clean()
        public = cleaned_data['public_content']
        private = cleaned_data['private_content']
        if not private and not public:
            missing_content = 'Must include either public or private content when submitting a report.'
            self.add_error('public_content', missing_content)
            self.add_error('private_content', missing_content)
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        is_draft = 'save' in self.data

        version = ReportVersion.objects.create(
            report=self.instance,
            public_content=self.cleaned_data['public_content'],
            private_content=self.cleaned_data['private_content'],
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

        removed_files = self.cleaned_data['file_list']
        ReportPrivateFiles.objects.bulk_create(
            ReportPrivateFiles(report=version, document=file.document)
            for file in self.report_files
            if file not in removed_files
        )

        added_files = self.cleaned_data['files']
        if added_files:
            ReportPrivateFiles.objects.bulk_create(
                ReportPrivateFiles(report=version, document=file)
                for file in added_files
            )

        return instance


class ReportFrequencyForm(forms.ModelForm):
    start = forms.DateField(label='Starting on:')

    class Meta:
        model = ReportConfig
        fields = ('occurrence', 'frequency', 'start')
        labels = {
            'occurrence': 'No.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        last_report = self.instance.last_report()

        self.fields['start'].widget.attrs.update({
            'min': max(
                last_report.end_date if last_report else today,
                today,
            ),
            'max': self.instance.project.end_date,
        })

    def clean_start(self):
        start_date = self.cleaned_data['start']
        last_report = self.instance.last_report()
        if last_report and start_date <= last_report.end_date:
            raise ValidationError(
                _("Cannot start a schedule before the current reporting period"),
                code="bad_start"
            )

        if start_date < timezone.now().date():
            raise ValidationError(
                _("Cannot start a schedule in the past"),
                code="bad_start"
            )

        if start_date > self.instance.project.end_date:
            raise ValidationError(
                _("Cannot start a schedule beyond the end date"),
                code="bad_start"
            )
        return start_date

    def save(self, *args, **kwargs):
        self.instance.schedule_start = self.cleaned_data['start']
        return super().save(*args, **kwargs)
