import copy

from django import template

register = template.Library()


@register.filter
def row_from_record(row, record):
    row = copy.copy(row)
    row._record = record
    return row
