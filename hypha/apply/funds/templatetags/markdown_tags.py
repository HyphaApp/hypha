import tomd
from django import template

from hypha.core.utils import markdown_to_html

register = template.Library()


@register.filter
def markdown(value):
    return markdown_to_html(value)


@register.filter
def to_markdown(value):
    # pass through markdown to ensure comment is a
    # fully formed HTML block
    value = markdown_to_html(value)
    return tomd.convert(value)
