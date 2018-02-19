from django.forms import FileInput, FileField


class MultiFileInput(FileInput):
    def __init__(self, *args, attrs={}, **kwargs):
        attrs['multiple'] = True
        super().__init__(*args, attrs=attrs, **kwargs)

    def value_from_datadict(self, data, files, name):
        "File widgets take data from FILES, not POST"
        return files.getlist(name)


class MultiFileField(FileField):
    widget = MultiFileInput

    def clean(self, value, initial):
        return [FileField().clean(file, initial) for file in value]
