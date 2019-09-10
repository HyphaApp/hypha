from django import template

register = template.Library()

# Get the verbose name of a wagtail page
@register.filter
def model_verbose_name(instance):
    return instance._meta.verbose_name.title()
