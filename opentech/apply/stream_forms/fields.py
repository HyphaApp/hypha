from django.forms import ClearableFileInput, FileField, CheckboxInput


class MultiFileInput(ClearableFileInput):
    """
    File Input only returns one file from its clean method.

    This passes all files through the clean method and means we have a list of
    files available for post processing
    """
    template_name = 'stream_forms/fields/multi_file_field.html'

    input_text = ''

    def __init__(self, *args, **kwargs):
        self.multiple = kwargs.pop('multiple', True)
        super().__init__(*args, **kwargs)

    def is_initial(self, value):
        is_initial = super().is_initial
        if not value:
            return False

        try:
            return all(
                is_initial(file) for file in value
            )
        except TypeError:
            return is_initial(value)

    def render(self, name, value, attrs=dict()):
        if self.multiple:
            attrs['multiple'] = 'multiple'

        return super().render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            upload = files.getlist(name)
        else:
            upload = files.get(name)
            if not isinstance(upload, list):
                upload = [upload]

        checkbox_name = self.clear_checkbox_name(name) + '-'
        checkboxes = {k for k in data if checkbox_name in k}
        cleared = {
            int(checkbox.replace(checkbox_name, '')) for checkbox in checkboxes
            if CheckboxInput().value_from_datadict(data, files, checkbox)
        }

        return {
            'files': upload,
            'cleared': cleared,
        }


class MultiFileField(FileField):
    widget = MultiFileInput

    def clean(self, value, initial):
        files = value['files']
        cleared = value['cleared']
        if not files and not cleared:
            return initial
        new = [FileField().clean(file, initial) for file in files]

        if initial:
            old = [file for i, file in enumerate(initial) if i not in cleared]
        else:
            old = []

        return old + new
