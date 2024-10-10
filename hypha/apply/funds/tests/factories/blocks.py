import json
import random

import factory

from hypha.apply.funds import blocks
from hypha.apply.stream_forms.testing.factories import (
    BLOCK_FACTORY_DEFINITION,
    FormFieldBlockFactory,
    ParagraphBlockFactory,
    StreamFieldUUIDFactory,
)
from hypha.apply.utils.testing.factories import RichTextFieldBlockFactory

__all__ = [
    "CustomFormFieldsFactory",
    "TitleBlockFactory",
    "EmailBlockFactory",
    "FullNameBlockFactory",
    "ValueFieldBlockFactory",
]


class TitleBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker("sentence")

    class Meta:
        model = blocks.TitleBlock


class EmailBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker("email")

    class Meta:
        model = blocks.EmailBlock


class FullNameBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker("name")

    class Meta:
        model = blocks.FullNameBlock


class DurationBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.DurationBlock

    @classmethod
    def make_answer(cls, params=None):
        choices = list(blocks.DurationBlock.DURATION_MONTH_OPTIONS.keys())
        return random.choice(choices)


class ValueFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ValueBlock

    @classmethod
    def make_answer(cls, params=None, form=False):
        return random.randint(0, 1_000_000)


class AddressFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.AddressFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        if not params:
            params = {}
        return json.dumps(
            {
                "country": "GB",
                "thoroughfare": factory.Faker("street_name").evaluate(
                    None, None, dict(params, locale=None)
                ),
                "premise": factory.Faker("building_number").evaluate(
                    None, None, dict(params, locale=None)
                ),
                "localityname": factory.Faker("city").evaluate(
                    None, None, dict(params, locale=None)
                ),
                "administrativearea": factory.Faker("city").evaluate(
                    None, None, dict(params, locale=None)
                ),
                "postalcode": "SW1 4AQ",
            }
        )

    @classmethod
    def make_form_answer(cls, params=None):
        if params is None:
            params = ""
        try:
            address = json.loads(params)
        except TypeError:
            if not params:
                params = {}
            return {
                "country": "GB",
                "thoroughfare": factory.Faker("street_name").evaluate(
                    None, None, dict(params, locale=None)
                ),
                "premise": factory.Faker("building_number").evaluate(
                    None, None, dict(params, locale=None)
                ),
                "locality": {
                    "localityname": factory.Faker("city").evaluate(
                        None, None, dict(params, locale=None)
                    ),
                    "administrativearea": factory.Faker("city").evaluate(
                        None, None, dict(params, locale=None)
                    ),
                    "postal_code": "SW1 4AQ",
                },
            }

        address["locality"] = {
            "localityname": address.pop("localityname"),
            "administrativearea": address.pop("administrativearea"),
            "postalcode": address.pop("postalcode"),
        }
        return address


CustomFormFieldsFactory = StreamFieldUUIDFactory(
    {
        **BLOCK_FACTORY_DEFINITION,
        "duration": factory.SubFactory(DurationBlockFactory),
        "title": factory.SubFactory(TitleBlockFactory),
        "value": factory.SubFactory(ValueFieldBlockFactory),
        "email": factory.SubFactory(EmailBlockFactory),
        "address": factory.SubFactory(AddressFieldBlockFactory),
        "full_name": factory.SubFactory(FullNameBlockFactory),
        "text_markup": factory.SubFactory(ParagraphBlockFactory),
        "rich_text": factory.SubFactory(RichTextFieldBlockFactory),
    }
)
