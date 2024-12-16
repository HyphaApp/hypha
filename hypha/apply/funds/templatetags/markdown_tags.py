from django import template

from hypha.core.utils import markdown_to_html

register = template.Library()


@register.filter
def markdown(value):
    return markdown_to_html(value)
