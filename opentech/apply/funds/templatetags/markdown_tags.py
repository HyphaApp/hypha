import mistune

from django import template

register = template.Library()


@register.filter
def markdown(value):
    markdown = mistune.Markdown()
    return markdown(value)
