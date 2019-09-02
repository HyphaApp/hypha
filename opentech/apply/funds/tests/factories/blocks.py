import json
import random
import factory

from opentech.apply.funds import blocks
from opentech.apply.stream_forms.testing.factories import (
    BLOCK_FACTORY_DEFINITION,
    FormFieldBlockFactory,
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
        choices = list(blocks.DurationBlock.DURATION_MONTH_OPTIONS.keys())
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
    def make_answer(cls, params):
        if not params:
            params = {}
        return json.dumps({
            'country': 'GB',
            'thoroughfare': factory.Faker('street_name').generate(params),
            'premise': factory.Faker('building_number').generate(params),
            'localityname': factory.Faker('city').generate(params),
            'administrativearea': factory.Faker('city').generate(params),
            'postalcode': 'SW1 4AQ',
        })

    @classmethod
    def make_form_answer(cls, params=dict()):
        try:
            address = json.loads(params)
        except TypeError:
            if not params:
                params = {}
            return {
                'country': 'GB',
                'thoroughfare': factory.Faker('street_name').generate(params),
                'premise': factory.Faker('building_number').generate(params),
                'locality': {
                    'localityname': factory.Faker('city').generate(params),
                    'administrativearea': factory.Faker('city').generate(params),
                    'postal_code': 'SW1 4AQ',
                }
            }

        address['locality'] = {
            'localityname': address.pop('localityname'),
            'administrativearea': address.pop('administrativearea'),
            'postalcode': address.pop('postalcode'),
        }
        return address


CustomFormFieldsFactory = StreamFieldUUIDFactory({
    **BLOCK_FACTORY_DEFINITION,
    'duration': DurationBlockFactory,
    'title': TitleBlockFactory,
    'value': ValueFieldBlockFactory,
    'email': EmailBlockFactory,
    'address': AddressFieldBlockFactory,
    'full_name': FullNameBlockFactory,
    'text_markup': ParagraphBlockFactory,
    'rich_text': RichTextFieldBlockFactory,
})
