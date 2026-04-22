import json

import pytest
from django.core.exceptions import ValidationError
from django.http import QueryDict

from .fields import AddressField, flatten_data
from .widgets import AddressWidget


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


# ---------------------------------------------------------------------------
# Existing validation tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Storage and retrieval (to_python / prepare_value round-trip)
# ---------------------------------------------------------------------------


def test_to_python_serialises_dict_to_json(address_field):
    address_data = {"country": "GB", "thoroughfare": "10 Downing Street"}
    result = address_field.to_python(address_data)
    assert result == json.dumps(address_data)


def test_prepare_value_deserialises_json_string(address_field):
    address_data = {"country": "GB", "thoroughfare": "10 Downing Street"}
    json_string = json.dumps(address_data)
    result = address_field.prepare_value(json_string)
    assert result == address_data


def test_round_trip_preserves_all_fields(address_field):
    address_data = {
        "country": "US",
        "thoroughfare": "1600 Pennsylvania Ave NW",
        "premise": "Suite 100",
        "localityname": "Washington",
        "administrativearea": "DC",
        "postalcode": "20500",
    }
    stored = address_field.to_python(address_data)
    retrieved = address_field.prepare_value(stored)
    assert retrieved == address_data


def test_prepare_value_empty_string_returns_empty_string(address_field):
    # json.loads({}) raises TypeError so the original value is returned as-is.
    result = address_field.prepare_value("")
    assert result == ""


def test_prepare_value_none_returns_none(address_field):
    # json.loads({}) raises TypeError so the original value is returned as-is.
    result = address_field.prepare_value(None)
    assert result is None


def test_prepare_value_passthrough_dict(address_field):
    # When the value is already a dict (not yet serialised), return it as-is.
    address_data = {"country": "GB"}
    result = address_field.prepare_value(address_data)
    assert result == address_data


# ---------------------------------------------------------------------------
# Validation against real country data
# ---------------------------------------------------------------------------


def test_invalid_country_raises_validation_error(address_field):
    with pytest.raises(ValidationError, match="Invalid country"):
        address_field.clean({"country": "XX"})


def test_gb_valid_address(address_field):
    address_field.clean(
        {
            "country": "GB",
            "thoroughfare": "10 Downing Street",
            "localityname": "London",
            "postalcode": "SW1A 2AA",
        }
    )


def test_gb_missing_required_thoroughfare(address_field):
    with pytest.raises(ValidationError):
        address_field.clean(
            {
                "country": "GB",
                "localityname": "London",
                "postalcode": "SW1A 2AA",
            }
        )


def test_gb_missing_required_postalcode(address_field):
    with pytest.raises(ValidationError):
        address_field.clean(
            {
                "country": "GB",
                "thoroughfare": "10 Downing Street",
                "localityname": "London",
            }
        )


def test_us_requires_state(address_field):
    with pytest.raises(ValidationError):
        address_field.clean(
            {
                "country": "US",
                "thoroughfare": "1600 Pennsylvania Ave NW",
                "localityname": "Washington",
                "postalcode": "20500",
                # administrativearea (state) missing
            }
        )


def test_us_valid_address(address_field):
    address_field.clean(
        {
            "country": "US",
            "thoroughfare": "1600 Pennsylvania Ave NW",
            "localityname": "Washington",
            "administrativearea": "DC",
            "postalcode": "20500",
        }
    )


def test_al_no_postalcode_required(address_field):
    # Albania (AL) only requires thoroughfare and localityname — no postalcode.
    address_field.clean(
        {
            "country": "AL",
            "thoroughfare": "Rruga e Dibres",
            "localityname": "Tirana",
        }
    )


# ---------------------------------------------------------------------------
# Dynamic fields: country-specific field configuration (VALIDATION_DATA)
# ---------------------------------------------------------------------------


def test_validation_data_loaded(address_field):
    # The real data should contain well-known countries.
    for iso in ("GB", "US", "AL", "AF"):
        assert iso in address_field.data


def test_gb_has_postalcode_field(address_field):
    gb = address_field.data["GB"]
    fields = flatten_data(gb["fields"])
    assert "postalcode" in fields


def test_gb_postalcode_label(address_field):
    gb = address_field.data["GB"]
    fields = flatten_data(gb["fields"])
    assert fields["postalcode"]["label"] == "Postcode"


def test_us_has_administrativearea_field(address_field):
    us = address_field.data["US"]
    fields = flatten_data(us["fields"])
    assert "administrativearea" in fields


def test_us_administrativearea_label(address_field):
    us = address_field.data["US"]
    fields = flatten_data(us["fields"])
    assert fields["administrativearea"]["label"] == "State"


def test_gb_and_us_have_different_required_fields(address_field):
    gb_required = set(address_field.data["GB"]["required"])
    us_required = set(address_field.data["US"]["required"])
    # US additionally requires administrativearea; GB does not.
    assert "administrativearea" in us_required
    assert "administrativearea" not in gb_required


def test_country_fields_differ_by_country(address_field):
    # Different countries expose different field sets.
    gb_fields = set(flatten_data(address_field.data["GB"]["fields"]).keys())
    al_fields = set(flatten_data(address_field.data["AL"]["fields"]).keys())
    # Albania has no postalcode field at all; GB does.
    assert "postalcode" in gb_fields
    assert "postalcode" not in al_fields


# ---------------------------------------------------------------------------
# flatten_data helper
# ---------------------------------------------------------------------------


def test_flatten_data_simple():
    data = [
        {"thoroughfare": {"label": "Address 1"}},
        {"premise": {"label": "Address 2"}},
    ]
    result = flatten_data(data)
    assert result == {
        "thoroughfare": {"label": "Address 1"},
        "premise": {"label": "Address 2"},
    }


def test_flatten_data_nested_list():
    data = [
        {
            "locality": [
                {"localityname": {"label": "City"}},
                {"postalcode": {"label": "Postal code"}},
            ]
        }
    ]
    result = flatten_data(data)
    assert "localityname" in result
    assert "postalcode" in result


# ---------------------------------------------------------------------------
# Widget: decompress (display stored value in form)
# ---------------------------------------------------------------------------


def test_widget_decompress_returns_list_of_values():
    widget = AddressWidget()
    value = {
        "country": "GB",
        "thoroughfare": "10 Downing Street",
        "premise": "",
        "localityname": "London",
        "administrativearea": "",
        "postalcode": "SW1A 2AA",
    }
    result = widget.decompress(value)
    assert isinstance(result, list)
    # First component is country
    assert result[0] == "GB"
    # Second component is thoroughfare
    assert result[1] == "10 Downing Street"


def test_widget_decompress_none_returns_nones():
    widget = AddressWidget()
    result = widget.decompress(None)
    assert all(v is None for v in result)


def test_widget_decompress_preserves_locality():
    widget = AddressWidget()
    value = {
        "country": "US",
        "thoroughfare": "1600 Pennsylvania Ave NW",
        "premise": "",
        "localityname": "Washington",
        "administrativearea": "DC",
        "postalcode": "20500",
    }
    result = widget.decompress(value)
    # The locality sub-widget is index 3; its decompress returns a list.
    locality = result[3]
    assert isinstance(locality, list)
    assert "Washington" in locality
    assert "DC" in locality
    assert "20500" in locality


# ---------------------------------------------------------------------------
# Widget: value_from_datadict (read submitted form data)
# ---------------------------------------------------------------------------


def test_widget_value_from_datadict_collects_fields():
    widget = AddressWidget()
    # AddressWidget has components: country(0), thoroughfare(1), premise(2), locality(3)
    # locality has: localityname(0), administrativearea(1), postalcode(2)
    post_data = QueryDict(
        "address_0=GB"
        "&address_1=10+Downing+Street"
        "&address_2="
        "&address_3_0=London"
        "&address_3_1="
        "&address_3_2=SW1A+2AA"
    )
    result = widget.value_from_datadict(post_data, {}, "address")
    assert result["country"] == "GB"
    assert result["thoroughfare"] == "10 Downing Street"
    assert result["localityname"] == "London"
    assert result["postalcode"] == "SW1A 2AA"


def test_widget_value_from_datadict_empty_submission():
    widget = AddressWidget()
    post_data = QueryDict(
        "address_0=&address_1=&address_2=&address_3_0=&address_3_1=&address_3_2="
    )
    result = widget.value_from_datadict(post_data, {}, "address")
    assert result["country"] == ""
    assert result["thoroughfare"] == ""
    assert result["postalcode"] == ""
