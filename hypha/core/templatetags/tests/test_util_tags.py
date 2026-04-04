"""Tests for core/templatetags/util_tags.py."""

import uuid

from django import forms
from django.test import SimpleTestCase

from hypha.core.templatetags.util_tags import field_type, generate_uuid, widget_type


class _SimpleForm(forms.Form):
    text_field = forms.CharField()
    choice_field = forms.ChoiceField(choices=[("a", "A")])
    checkbox = forms.BooleanField(required=False)


class TestGenerateUuid(SimpleTestCase):
    def test_returns_string(self):
        self.assertIsInstance(generate_uuid(), str)

    def test_returns_valid_uuid(self):
        result = generate_uuid()
        # Should not raise
        parsed = uuid.UUID(result)
        self.assertEqual(str(parsed), result)

    def test_each_call_returns_unique_value(self):
        self.assertNotEqual(generate_uuid(), generate_uuid())


class TestWidgetType(SimpleTestCase):
    def _bound(self, field_name):
        form = _SimpleForm()
        return form[field_name]

    def test_text_field_widget_type(self):
        result = widget_type(self._bound("text_field"))
        self.assertEqual(result, "text_input")

    def test_select_widget_type(self):
        result = widget_type(self._bound("choice_field"))
        self.assertEqual(result, "select")

    def test_checkbox_widget_type(self):
        result = widget_type(self._bound("checkbox"))
        self.assertEqual(result, "checkbox_input")


class TestFieldType(SimpleTestCase):
    def _bound(self, field_name):
        form = _SimpleForm()
        return form[field_name]

    def test_char_field_type(self):
        result = field_type(self._bound("text_field"))
        self.assertEqual(result, "char_field")

    def test_choice_field_type(self):
        result = field_type(self._bound("choice_field"))
        self.assertEqual(result, "choice_field")

    def test_boolean_field_type(self):
        result = field_type(self._bound("checkbox"))
        self.assertEqual(result, "boolean_field")
