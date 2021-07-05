from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import FileExtensionValidator
from django.forms import FileField, Media
from django.utils.functional import cached_property
from django_file_form.fields import MultipleUploadedFileField, UploadedFileField
from django_file_form.widgets import UploadMultipleWidget, UploadWidget


class FileFieldWidgetMixin:

    # This file seems to be imported even during collectstatic,
    # at which point `static()` won't be able to find these files yet
    # using production settings, so we delay calling `static()` until it's needed.
    @cached_property
    def media(self):
        return Media(
            css={'all': [
                static('file_form/file_form.css'),
            ]},
            js=[
                static('file_form/file_form.js'),
                static('js/apply/file-uploads.js'),
            ],
        )


class MultiFileFieldWidget(FileFieldWidgetMixin, UploadMultipleWidget):
    pass


class MultiFileField(MultipleUploadedFileField):
    widget = MultiFileFieldWidget

    def clean(self, value, initial):
        if not value:
            return []
        old_files = [
            file for file in value
            if hasattr(file, 'is_placeholder') and file.is_placeholder
        ]
        new_files = [
            file for file in value
            if hasattr(file, 'is_placeholder') and not file.is_placeholder
        ]
        if not new_files and initial and len(old_files) == len(initial):
            return initial

        files = [
            FileField(validators=[
                FileExtensionValidator(allowed_extensions=settings.FILE_ALLOWED_EXTENSIONS)
            ]).clean(file, initial) for file in value
        ]

        return files

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, MultiFileFieldWidget) and 'accept' not in widget.attrs:
            attrs.setdefault('accept', settings.FILE_ACCEPT_ATTR_VALUE)
        return attrs


class SingleFileFieldWidget(FileFieldWidgetMixin, UploadWidget):
    pass


class SingleFileField(UploadedFileField):
    widget = SingleFileFieldWidget

    def clean(self, value, initial):
        if not value:
            return
        if hasattr(value, 'is_placeholder') and value.is_placeholder and initial:
            return initial
        validator = FileExtensionValidator(allowed_extensions=settings.FILE_ALLOWED_EXTENSIONS)
        file = FileField(validators=[validator]).clean(value, initial)
        return file

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, SingleFileFieldWidget) and 'accept' not in widget.attrs:
            attrs.setdefault('accept', settings.FILE_ACCEPT_ATTR_VALUE)
        return attrs
