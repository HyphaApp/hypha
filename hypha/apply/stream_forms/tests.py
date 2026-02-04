from django.test import TestCase
from faker import Faker

from .blocks import FormFieldBlock, FormFieldsBlock

fake = Faker()


class TestBlocks(TestCase):
    def test_blocks_decode_none(self):
        for block in FormFieldsBlock().child_blocks.values():
            if isinstance(block, FormFieldBlock):
                with self.subTest(block=block.__class__.__name__):
                    value = block.decode(None)
                    self.assertIsNone(value)
