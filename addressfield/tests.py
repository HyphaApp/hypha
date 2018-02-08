from django.core.exceptions import ValidationError
from django.test import TestCase

from .fields import AddressField


class TestRequiredFields(TestCase):
    def build_validation_data(self, fields=list(), required=list()):
        fields = set(fields + required)
        return {'COUNTRY': {
            'fields': [{field: {'label': field}} for field in fields],
            'required': required,
        }}

    def test_non_required(self):
        field = AddressField()
        field.data = self.build_validation_data(fields=['postalcode'])
        field.clean({'country': 'COUNTRY'})

    def test_non_required_blank_data(self):
        field = AddressField()
        field.data = self.build_validation_data(fields=['postalcode'])
        field.clean({'country': 'COUNTRY', 'postalcode': ''})

    def test_one_field_required(self):
        field = AddressField()
        field.data = self.build_validation_data(required=['postalcode'])
        with self.assertRaises(ValidationError):
            field.clean({'country': 'COUNTRY'})

    def test_one_field_required_blank_data(self):
        field = AddressField()
        field.data = self.build_validation_data(required=['postalcode'])
        with self.assertRaises(ValidationError):
            field.clean({'country': 'COUNTRY', 'postalcode': ''})

    def test_one_field_required_supplied_data(self):
        field = AddressField()
        field.data = self.build_validation_data(required=['postalcode'])
        field.clean({'country': 'COUNTRY', 'postalcode': 'BS1 2AB'})
