from django import template

from ..models import CookieConsentSettings

register = template.Library()


@register.inclusion_tag("includes/banner.html", takes_context=True)
def cookie_banner(context):
    request = context["request"]
    settings = CookieConsentSettings.load(request_or_site=request)
    show_banner = settings.cookieconsent_active and not request.COOKIES.get(
        "cookieconsent"
    )

    return {
        "show_banner": show_banner,
        "title": settings.cookieconsent_title,
        "message": settings.cookieconsent_message,
    }
