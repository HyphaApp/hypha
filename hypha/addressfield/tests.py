import pytest
from django.core.exceptions import ValidationError

from .fields import AddressField


def build_validation_data(fields=None, required=None):
    fields = fields or []
    required = required or []
    return {
        "COUNTRY": {
            "fields": [{field: {"label": field}} for field in set(fields + required)],
            "required": required,
        }
    }


@pytest.fixture
def address_field():
    return AddressField()


def test_non_required(address_field):
    address_field.data = build_validation_data(fields=["postalcode"])
    address_field.clean({"country": "COUNTRY"})


def test_non_required_blank_data(address_field):
    address_field.data = build_validation_data(fields=["postalcode"])
    address_field.clean({"country": "COUNTRY", "postalcode": ""})


def test_one_field_required(address_field):
    address_field.data = build_validation_data(required=["postalcode"])
    with pytest.raises(ValidationError):
        address_field.clean({"country": "COUNTRY"})


def test_one_field_required_blank_data(address_field):
    address_field.data = build_validation_data(required=["postalcode"])
    with pytest.raises(ValidationError):
        address_field.clean({"country": "COUNTRY", "postalcode": ""})


def test_one_field_required_supplied_data(address_field):
    address_field.data = build_validation_data(required=["postalcode"])
    address_field.clean({"country": "COUNTRY", "postalcode": "BS1 2AB"})
