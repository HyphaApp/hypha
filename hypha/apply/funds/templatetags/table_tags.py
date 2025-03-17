import copy
import math

from django import forms, template
from django_filters.fields import DateRangeField

from hypha.apply.categories.models import MetaTerm
from hypha.apply.users.models import User

register = template.Library()


@register.simple_tag
def prepare_query_data(key, value):
    return "{key}={value}".format(key=key, value=value)


@register.simple_tag
def get_filtered_query(request, form):
    query_list = []
    for key, values in request.GET.lists():
        field = form.fields.get(key)
        if not field:
            # Handle DateRangePicker
            if "_after" in key or "_before" in key:
                for value in values:
                    query_list.append(
                        {key: {"value": value, "label": value, "key_label": key}}
                    )
            continue

        choices_dict = {}
        # Handle ModelChoiceField (for ModelMultipleChoiceFilter)
        if hasattr(field, "queryset"):
            choices_dict = {str(obj.pk): str(obj) for obj in field.queryset}
        # Handle ChoiceField (for MultipleChoiceFilter)
        elif hasattr(field, "choices"):
            choices_dict = dict(field.choices)

        for value in values:
            label = choices_dict.get(str(value), value)
            query_list.append(
                {key: {"value": value, "label": label, "key_label": field.label}}
            )
    return query_list


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
def is_multiple(field):
    return field.widget.allow_multiple_selected


@register.filter
def is_datefilter(field):
    if isinstance(field, DateRangeField):
        return True
    return False


@register.filter
def get_filter_fields(form):
    fields = []
    for field_name, field in form.fields.items():
        if not isinstance(field.widget, forms.HiddenInput):
            fields.append((field_name, field))
    return fields


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
