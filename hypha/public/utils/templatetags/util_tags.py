from django import template
from wagtail.coreutils import camelcase_to_underscore

register = template.Library()


# Get widget type of a field
@register.filter(name="widget_type")
def widget_type(bound_field):
    return camelcase_to_underscore(bound_field.field.widget.__class__.__name__)


# Get type of field
@register.filter(name="field_type")
def field_type(bound_field):
    return camelcase_to_underscore(bound_field.field.__class__.__name__)


# Get the verbose name of a wagtail page
@register.simple_tag
def verbose_name(instance):
    return instance.specific._meta.verbose_name.title()
