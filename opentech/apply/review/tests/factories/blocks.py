import json
import random
import uuid

import factory
from wagtail.core.blocks import CharBlock
import wagtail_factories

from opentech.apply.stream_forms import blocks as stream_blocks
from opentech.apply.review import blocks


class CharBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = CharBlock


class FormFieldBlockFactory(wagtail_factories.StructBlockFactory):
    default_value = factory.Faker('word')

    class Meta:
        model = stream_blocks.FormFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.default_value.generate(params)


class CharFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker('sentence')

    class Meta:
        model = stream_blocks.CharFieldBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RichTextFieldBlock


class RecommendationBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RecommendationBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.choices[0]


class RecommendationCommentsBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RecommendationCommentsBlock


class ScoreFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ScoreFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return json.dumps([random.randint(0, 5), factory.Faker('word').generate(params)])


class StreamFieldUUIDFactory(wagtail_factories.StreamFieldFactory):
    def generate(self, *args, **kwargs):
        blocks = super().generate(*args, **kwargs)
        ret_val = list()
        # Convert to JSON so we can add id before create
        for block_name, value in blocks:
            block = self.factories[block_name]._meta.model()
            value = block.get_prep_value(value)
            ret_val.append({'type': block_name, 'value': value, 'id': str(uuid.uuid4())})
        return json.dumps(ret_val)


ReviewFormFieldsFactory = StreamFieldUUIDFactory({
    'char': CharFieldBlockFactory,
    'rich_text': RichTextFieldBlockFactory,
})
