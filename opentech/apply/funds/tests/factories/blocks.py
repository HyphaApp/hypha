import json
import random
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile

import factory
from wagtail.core.blocks import CharBlock
import wagtail_factories

from opentech.apply.stream_forms import blocks as stream_blocks
from opentech.apply.funds import blocks


__all__ = ['CustomFormFieldsFactory', 'FormFieldBlockFactory', 'FullNameBlockFactory', 'EmailBlockFactory']


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


class NumberFieldBlockFactory(FormFieldBlockFactory):
    default_value = 100

    class Meta:
        model = stream_blocks.NumberFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.default_value


class RadioFieldBlockFactory(FormFieldBlockFactory):
    choices = ['first', 'second']

    class Meta:
        model = stream_blocks.RadioButtonsFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.choices[0]


class UploadableMediaFactory(FormFieldBlockFactory):
    default_value = factory.django.FileField

    @classmethod
    def make_answer(cls, params=dict()):
        file_name, file = cls.default_value()._make_content(params)
        return InMemoryUploadedFile(file, 'file', file_name, None, file.tell(), None)


class ImageFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.ImageFieldBlock


class FileFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.FileFieldBlock


class MultiFileFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.MultiFileFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return [UploadableMediaFactory.make_answer() for _ in range(2)]


class TitleBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker('sentence')

    class Meta:
        model = blocks.TitleBlock


class EmailBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker('email')

    class Meta:
        model = blocks.EmailBlock


class FullNameBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker('name')

    class Meta:
        model = blocks.FullNameBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RichTextFieldBlock


class ValueFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ValueBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return random.randint(0, 1_000_000)


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


CustomFormFieldsFactory = StreamFieldUUIDFactory({
    'title': TitleBlockFactory,
    'value': ValueFieldBlockFactory,
    'email': EmailBlockFactory,
    'full_name': FullNameBlockFactory,
    'char': CharFieldBlockFactory,
    'number': NumberFieldBlockFactory,
    'radios': RadioFieldBlockFactory,
    'rich_text': RichTextFieldBlockFactory,
    'image': ImageFieldBlockFactory,
    'file': FileFieldBlockFactory,
    'multi_file': MultiFileFieldBlockFactory,
})
