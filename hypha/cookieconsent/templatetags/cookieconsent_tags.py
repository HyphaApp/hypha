from django import template
from wagtail.models import Site

from ..models import CookieConsentSettings

register = template.Library()


@register.inclusion_tag("includes/banner.html", takes_context=True)
def cookie_banner(context):
    request = context["request"]
    site = Site.find_for_request(request)
    cookieconsent_settings = CookieConsentSettings.for_site(site=site)
    show_banner = (
        cookieconsent_settings.cookieconsent_active
        and not request.COOKIES.get("cookieconsent")
    )

    return {
        "show_banner": show_banner,
        "title": cookieconsent_settings.cookieconsent_title,
        "message": cookieconsent_settings.cookieconsent_message,
    }
