from django.test import TestCase

from opentech.apply.categories.blocks import CategoryQuestionBlock

from .factories import CategoryFactory


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
