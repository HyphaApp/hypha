import copy
import math

from django import template

from hypha.apply.categories.models import MetaTerm
from hypha.apply.users.models import User

register = template.Library()


@register.simple_tag
def prepare_query_data(key, value):
    return "{key}={value}".format(key=key, value=value)


@register.simple_tag
def get_item_value(form, key):
    return form[key].value()


@register.filter
def get_field_choices(form, field_name):
    """Returns the choices of a form field."""
    if hasattr(form[field_name].field, "choices"):
        return form[field_name].field.choices if field_name in form.fields else []
    return []


@register.filter
def row_from_record(row, record):
    row = copy.copy(row)
    row._record = record
    return row


@register.simple_tag
def total_num_of_pages(total_no_of_rows, per_page):
    return math.ceil(total_no_of_rows / per_page)


@register.filter
def get_display_name_from_id(user_id: int) -> str:
    return User.objects.get(id=user_id).get_display_name()


@register.filter
def get_meta_term_from_id(meta_term_id: int) -> str:
    return MetaTerm.objects.get(id=meta_term_id).name
