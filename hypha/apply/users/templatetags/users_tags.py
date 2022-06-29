from django import template
from django_otp import devices_for_user

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


@register.simple_tag
def user_2fa_enabled(user):
    """Checking if 2FA devices exist for the user"""
    if len(list(devices_for_user(user))):
        return True
    return False


@register.simple_tag
def tokens_text(token_set):
    tokens_string = ""
    for token in token_set:
        tokens_string += str(token.token) + " \n"
    return tokens_string
