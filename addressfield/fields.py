import json
from os import path

from django import forms
from django.core.exceptions import ValidationError

from .widgets import AddressWidget


basepath = path.dirname(__file__)
filepath = path.abspath(path.join(basepath, "static", "addressfield.min.json"))
with open(filepath, encoding='utf8') as address_data:
    countries = json.load(address_data)['options']

VALIDATION_DATA = {country['iso']: country for country in countries}


def flatten_data(data):
    flattened = dict()
    for d in data:
        for k, v in d.items():
            if isinstance(v, list):
                value = flatten_data(v)
            else:
                value = {k: v}
            flattened.update(value)
    return flattened


class AddressField(forms.CharField):
    widget = AddressWidget

    def clean(self, value, **kwargs):
        country = value['country']
        try:
            country_data = VALIDATION_DATA[country]
        except KeyError:
            raise ValidationError('Invalid country selected')

        fields = flatten_data(country_data['fields'])

        missing_fields = set(country_data['required']) - set(value.keys())
        if missing_fields:
            missing_field_name = [fields[field]['label'] for field in missing_fields]
            raise ValidationError('Please provide data for: {}'.format(', '.join(missing_field_name)))

        super().clean(value, **kwargs)
