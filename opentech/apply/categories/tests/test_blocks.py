from django import forms
from django.test import TestCase

from opentech.apply.categories.blocks import CategoryQuestionBlock

from .factories import CategoryFactory, OptionFactory


class TestCategoryQuestionBlock(TestCase):
    @classmethod
    def setUp(self):
        self.category = CategoryFactory()
        self.block = CategoryQuestionBlock()

    def get_field(self, **kwargs):
        data = {
            'field_label': '',
            'help_text': '',
            'category': self.category.id,
            'multi': False,
        }
        data.update(kwargs)

        block = self.block.to_python(data)

        return self.block.get_field(block)

    def test_field_and_help_default(self):
        field = self.get_field(field_label='', help_text='')
        self.assertEqual(self.category.name, field.label)
        self.assertEqual(self.category.help_text, field.help_text)

    def test_supplied_field_and_help(self):
        values = {'field_label': 'LABEL', 'help_text': 'HELP'}
        field = self.get_field(**values)
        self.assertEqual(values['field_label'], field.label)
        self.assertEqual(values['help_text'], field.help_text)

    def test_multi_select_enabled(self):
        field = self.get_field(multi=True)
        self.assertTrue(isinstance(field, forms.MultipleChoiceField))

    def test_multi_select_disabled(self):
        field = self.get_field(multi=True)
        self.assertTrue(isinstance(field, forms.ChoiceField))

    def test_options_included_in_choices(self):
        # Don't assign to variable as the ordering wont match choices
        OptionFactory.create_batch(3, category=self.category)
        field = self.get_field()
        self.assertEqual(
            field.choices,
            [(option.id, option.value) for option in self.category.options.all()]
        )

    def test_can_render_if_no_response(self):
        display = self.block.render({'category': self.category}, {'data': None})
        self.assertIn(self.block.no_response()[0], display)
