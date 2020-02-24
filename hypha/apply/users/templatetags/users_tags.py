from django import template

from ..utils import can_use_oauth_check

register = template.Library()


@register.filter
def backend_name(name):
    """Human readable mapping for the social auth backend"""
    return {
        'google-oauth': 'Google OAuth',
        'google-oauth2': 'Google OAuth',
        'google-openidconnect': 'Google OpenId',
    }.get(name, name)


@register.filter
def backend_class(backend):
    return backend.replace('-', ' ')


@register.simple_tag(takes_context=True)
def can_use_oauth(context):
    user = context.get('user')

    return can_use_oauth_check(user)
