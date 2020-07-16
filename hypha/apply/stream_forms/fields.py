from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import FileExtensionValidator
from django.forms import FileField, Media
from django.utils.functional import cached_property
from django_file_form.forms import MultipleUploadedFileField
from django_file_form.widgets import UploadMultipleWidget


class MultiFileFieldWidget(UploadMultipleWidget):

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


class MultiFileField(MultipleUploadedFileField):
    widget = MultiFileFieldWidget

    def clean(self, value, initial):
        validator = FileExtensionValidator(allowed_extensions=settings.FILE_ALLOWED_EXTENSIONS)

        for file in value:
            FileField(validators=[validator]).clean(file, initial)

        return super().clean(value, initial)

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        if isinstance(widget, MultiFileFieldWidget) and 'accept' not in widget.attrs:
            attrs.setdefault('accept', settings.FILE_ACCEPT_ATTR_VALUE)
        return attrs
