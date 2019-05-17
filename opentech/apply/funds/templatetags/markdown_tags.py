import mistune
import tomd

from django import template

register = template.Library()

mistune_markdown = mistune.Markdown()


@register.filter
def markdown(value):
    return mistune_markdown(value)


@register.filter
def to_markdown(value):
    # pass through markdown to ensure comment is a
    # fully formed HTML block
    value = markdown(value)
    return tomd.convert(value)
