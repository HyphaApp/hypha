import json
import random
import factory

from opentech.apply.funds import blocks
from opentech.apply.stream_forms.testing.factories import (
    CharFieldBlockFactory,
    FileFieldBlockFactory,
    FormFieldBlockFactory,
    ImageFieldBlockFactory,
    MultiFileFieldBlockFactory,
    NumberFieldBlockFactory,
    RadioFieldBlockFactory,
    ParagraphBlockFactory,
    StreamFieldUUIDFactory,
)
from opentech.apply.utils.testing.factories import RichTextFieldBlockFactory

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


class DurationBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.DurationBlock

    @classmethod
    def make_answer(cls, params=dict()):
        choices = list(blocks.DurationBlock.DURATION_OPTIONS.keys())
        return random.choice(choices)


class ValueFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ValueBlock

    @classmethod
    def make_answer(cls, params=dict(), form=False):
        return random.randint(0, 1_000_000)


class AddressFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.AddressFieldBlock

    @classmethod
    def an_adress(cls):
        return {
            'country': 'GB',
            'thoroughfare': 'bah',
            'premise': 'baz',
            'locality': {
                'locality_name': 'bish',
                'administrative_area': 'bosh',
                'postal_code': 'SW1 4AQ',
            }
        }

    @classmethod
    def make_answer(cls, params=dict()):
        return json.dumps({
            'country': 'GB',
            'thoroughfare': 'bah',
            'premise': 'baz',
            'localityname': 'bish',
            'administrativearea': 'bosh',
            'postalcode': 'SW1 4AQ',
        })

    @classmethod
    def make_form_answer(cls, params=dict()):
        return {
            'country': 'GB',
            'thoroughfare': 'bah',
            'premise': 'baz',
            'locality': {
                'locality_name': 'bish',
                'administrative_area': 'bosh',
                'postal_code': 'SW1 4AQ',
            }
        }


CustomFormFieldsFactory = StreamFieldUUIDFactory({
    'duration': DurationBlockFactory,
    'title': TitleBlockFactory,
    'value': ValueFieldBlockFactory,
    'email': EmailBlockFactory,
    'address': AddressFieldBlockFactory,
    'full_name': FullNameBlockFactory,
    'char': CharFieldBlockFactory,
    'number': NumberFieldBlockFactory,
    'radios': RadioFieldBlockFactory,
    'rich_text': RichTextFieldBlockFactory,
    'image': ImageFieldBlockFactory,
    'file': FileFieldBlockFactory,
    'multi_file': MultiFileFieldBlockFactory,
    'text_markup': ParagraphBlockFactory,
})
