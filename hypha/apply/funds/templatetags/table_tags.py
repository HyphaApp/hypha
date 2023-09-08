import copy
import math

from django import template

register = template.Library()


@register.filter
def row_from_record(row, record):
    row = copy.copy(row)
    row._record = record
    return row


@register.simple_tag
def total_num_of_pages(total_no_of_rows, per_page):
    return math.ceil(total_no_of_rows / per_page)
