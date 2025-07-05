from django import template

from ..models import CookieConsentSettings

register = template.Library()


@register.inclusion_tag("includes/banner.html", takes_context=True)
def cookie_banner(context):
    return {"settings": CookieConsentSettings.load(request_or_site=context["request"])}
