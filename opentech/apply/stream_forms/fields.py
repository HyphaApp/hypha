from django.forms import FileInput, FileField


class MultiFileInput(FileInput):
    """
    File Input only returns one file from its clean method.

    This passes all files through the clean method and means we have a list of
    files available for post processing
    """
    def __init__(self, *args, attrs={}, **kwargs):
        attrs['multiple'] = True
        super().__init__(*args, attrs=attrs, **kwargs)

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class MultiFileField(FileField):
    widget = MultiFileInput

    def clean(self, value, initial):
        return [FileField().clean(file, initial) for file in value]
