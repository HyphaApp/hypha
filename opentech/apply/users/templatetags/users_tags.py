from django import template
from django.conf import settings

register = template.Library()


@register.filter
def backend_name(name):
    return {
        'google-oauth': 'Google OAuth',
        'google-oauth2': 'Google OAuth',
        'google-openidconnect': 'Google OpenId',
        'facebook-app': 'Facebook',
        'stackoverflow': 'Stack Overflow',
        'yahoo-oauth': 'Yahoo',
        'vimeo': 'Vimeo',
        'linkedin-oauth2': 'LinkedIn OAuth',
        'vk-oauth2': 'VK OAuth',
        'live': 'Windows Live',
    }.get(name, name)


@register.filter
def backend_class(backend):
    return backend.replace('-', ' ')


@register.simple_tag(takes_context=True)
def can_use_oauth(context):
    user = context.get('user')

    try:
        if settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS:
            for domain in settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS:
                if user.email.endswith(f'@{domain}'):
                    return True
    except AttributeError:
        return False

    return False
