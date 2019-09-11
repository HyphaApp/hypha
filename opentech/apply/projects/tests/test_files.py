from django.core.files import File
from django.test import TestCase
from more_itertools import collapse

from opentech.apply.stream_forms.files import StreamFieldFile

from ..files import flatten, get_files
from .factories import ProjectFactory


class TestFlatten(TestCase):
    def test_no_items(self):
        with self.assertRaises(TypeError):
            list(flatten(1))

    def test_one_level_of_items(self):
        output = list(flatten([1, 2, 3]))
        self.assertEqual(output, [1, 2, 3])

    def test_two_levels_of_items(self):
        output = list(flatten([1, [2, 3]]))
        self.assertEqual(output, [1, 2, 3])

    def test_three_levels_of_items(self):
        output = list(flatten([1, [2, (3)]]))
        self.assertEqual(output, [1, 2, (3)])


class TestGetFiles(TestCase):
    def test_get_files(self):
        project = ProjectFactory()

        files = list(get_files(project))

        self.assertTrue(all(issubclass(f.__class__, File) for f in files))

        fields = project.submission.form_data.values()
        fields = collapse(fields, base_type=StreamFieldFile)
        fields = [f for f in fields if isinstance(f, StreamFieldFile)]

        self.assertEqual(len(files), len(fields))

        for f in files:
            self.assertIn(f, fields)
