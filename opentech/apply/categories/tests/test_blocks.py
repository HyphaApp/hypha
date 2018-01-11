from django.test import TestCase

from opentech.apply.categories.blocks import CategoryQuestionBlock

from .factories import CategoryFactory


class TestCategoryQuestionBlock(TestCase):
    @classmethod
    def setUp(self):
        self.category = CategoryFactory()
        self.block = CategoryQuestionBlock()

    def test_field_and_help_default(self):
        block = self.block.to_python({
            'field_label': '',
            'help_text': '',
            'category': self.category.id,
            'multi': False,
        })

        field = self.block.get_field(block)

        self.assertEqual(self.category.name, field.label)
        self.assertEqual(self.category.help_text, field.help_text)
