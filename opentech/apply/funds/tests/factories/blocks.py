import random
import factory

from opentech.apply.funds import blocks
from opentech.apply.stream_forms.tests.factories import FormFieldBlockFactory, CharFieldBlockFactory, \
    NumberFieldBlockFactory, RadioFieldBlockFactory, ImageFieldBlockFactory, FileFieldBlockFactory, \
    MultiFileFieldBlockFactory, StreamFieldUUIDFactory
from opentech.apply.utils.tests.factories import RichTextFieldBlockFactory

__all__ = ['CustomFormFieldsFactory', 'TitleBlockFactory', 'EmailBlockFactory', 'FullNameBlockFactory', 'ValueFieldBlockFactory']


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


class ValueFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ValueBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return random.randint(0, 1_000_000)


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
