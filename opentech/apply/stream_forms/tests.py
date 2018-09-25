from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from faker import Faker

from .files import StreamFieldFile
from .fields import MultiFileField, MultiFileInput

fake = Faker()


def make_files(number):
    file_names = [f'{fake.word()}_{i}' for i in range(3)]
    files = [
        StreamFieldFile(SimpleUploadedFile(name, b'Some File Content'), filename=name)
        for name in file_names
    ]
    return files


class TestMultiFileInput(TestCase):
    widget = MultiFileInput()

    def test_renders_multiple_attr(self):
        html = self.widget.render('', [])
        self.assertIn('multiple', html)

    def test_renders_multiple_files(self):
        files = make_files(3)
        html = self.widget.render('', files)
        for file in files:
            self.assertIn(file.filename, html)

    def test_handles_files(self):
        field_name = 'testing'
        files = make_files(3)
        files_data = {field_name: files}
        data = self.widget.value_from_datadict({}, files_data, field_name)
        self.assertEqual(data['files'], files)

    def test_no_delete(self):
        data = self.widget.value_from_datadict({}, {}, '')
        self.assertFalse(data['cleared'])

    def test_delete(self):
        field_name = 'testing'
        field_id = self.widget.clear_checkbox_name(field_name) + '-'
        form_data = {
            field_id + '0': 'on',
            field_id + '4': 'on',
        }
        data = self.widget.value_from_datadict(form_data, {}, field_name)
        self.assertEqual(data['cleared'], {0, 4})


class TestMultiFileField(TestCase):
    field = MultiFileField()

    def multi_file_value(self, files=list(), cleared=set()):
        return {
            'files': files,
            'cleared': cleared,
        }

    def test_returns_files_if_no_change(self):
        files = make_files(3)
        cleaned = self.field.clean(self.multi_file_value(), files)
        self.assertEqual(files, cleaned)

    def test_returns_new_files(self):
        files = make_files(3)
        cleaned = self.field.clean(self.multi_file_value(files=files), None)
        self.assertEqual(files, cleaned)

    def test_returns_inital_and_files(self):
        initial_files = make_files(3)
        new_files = make_files(3)
        cleaned = self.field.clean(self.multi_file_value(files=new_files), initial_files)
        self.assertEqual(initial_files + new_files, cleaned)

    def test_returns_nothing_all_cleared(self):
        initial_files = make_files(3)
        cleaned = self.field.clean(self.multi_file_value(cleared=range(3)), initial_files)
        self.assertEqual([], cleaned)

    def test_returns_something_some_cleared(self):
        initial_files = make_files(3)
        cleaned = self.field.clean(self.multi_file_value(cleared=[0, 2]), initial_files)
        self.assertEqual([initial_files[1]], cleaned)
