from django import template

register = template.Library()


@register.filter
def row_from_record(row, record):
    row._record = record
    return row
