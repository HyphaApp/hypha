from django import forms
from django.http import QueryDict
from django.test import TestCase
from django.urls import reverse
from faker import Faker

from .blocks import FormFieldBlock, FormFieldsBlock
from .forms import StreamBaseForm

fake = Faker()


class TestBlocks(TestCase):
    def test_blocks_decode_none(self):
        for block in FormFieldsBlock().child_blocks.values():
            if isinstance(block, FormFieldBlock):
                with self.subTest(block=block.__class__.__name__):
                    value = block.decode(None)
                    self.assertIsNone(value)


class TestStreamBaseForm(TestCase):
    def get_form(self, **kwargs):
        form_class = type(
            "TestForm", (StreamBaseForm,), {"title": forms.CharField(required=False)}
        )
        return form_class(**kwargs)

    def test_stored_file_form_fields_are_ignored_as_initial(self):
        form = self.get_form(
            initial={"upload_url": "/upload/upload/", "form_id": "old-form-id"}
        )
        self.assertEqual(form["upload_url"].value(), reverse("tus_upload"))
        self.assertNotEqual(form["form_id"].value(), "old-form-id")

    def test_file_form_fields_are_not_in_cleaned_data(self):
        form = self.get_form(
            data=QueryDict("title=A+title&upload_url=/upload/&form_id=abc")
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["title"], "A title")
        self.assertNotIn("upload_url", form.cleaned_data)
        self.assertNotIn("form_id", form.cleaned_data)
