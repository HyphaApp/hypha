from django import template

from wagtail.wagtailcore.utils import camelcase_to_underscore

from opentech.public.utils.models import SocialMediaSettings


register = template.Library()


# Social text
@register.filter(name='social_text')
def social_text(page, site):
    try:
        return page.social_text
    except AttributeError:
        return SocialMediaSettings.for_site(site).default_sharing_text


# Get widget type of a field
@register.filter(name='widget_type')
def widget_type(bound_field):
    return camelcase_to_underscore(bound_field.field.widget.__class__.__name__)


# Get type of field
@register.filter(name='field_type')
def field_type(bound_field):
    return camelcase_to_underscore(bound_field.field.__class__.__name__)


# Get the verbose name of a wagtail page
@register.simple_tag
def verbose_name(instance):
    return instance.specific._meta.verbose_name.title()
