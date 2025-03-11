from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.forms import FileField
from django_file_form.fields import MultipleUploadedFileField, UploadedFileField
from django_file_form.widgets import UploadMultipleWidget, UploadWidget


class MultiFileFieldWidget(UploadMultipleWidget):
    pass


class MultiFileField(MultipleUploadedFileField):
    widget = MultiFileFieldWidget

    def clean(self, value, initial):
        if not value:
            return []
        old_files = [
            file
            for file in value
            if hasattr(file, "is_placeholder") and file.is_placeholder
        ]
        new_files = [
            file
            for file in value
            if hasattr(file, "is_placeholder") and not file.is_placeholder
        ]
        if not new_files and initial and len(old_files) == len(initial):
            return initial

        files = [
            FileField(
                validators=[
                    FileExtensionValidator(
                        allowed_extensions=settings.FILE_ALLOWED_EXTENSIONS
                    )
                ]
            ).clean(file, initial)
            for file in value
        ]

        return files

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, MultiFileFieldWidget) and "accept" not in widget.attrs:
            attrs.setdefault("accept", settings.FILE_ACCEPT_ATTR_VALUE)
        return attrs


class SingleFileFieldWidget(UploadWidget):
    pass


class SingleFileField(UploadedFileField):
    widget = SingleFileFieldWidget

    def clean(self, value, initial):
        if not value:
            return
        if hasattr(value, "is_placeholder") and value.is_placeholder and initial:
            return initial
        validator = FileExtensionValidator(
            allowed_extensions=settings.FILE_ALLOWED_EXTENSIONS
        )
        file = FileField(validators=[validator]).clean(value, initial)
        return file

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, SingleFileFieldWidget) and "accept" not in widget.attrs:
            attrs.setdefault("accept", settings.FILE_ACCEPT_ATTR_VALUE)
        return attrs
