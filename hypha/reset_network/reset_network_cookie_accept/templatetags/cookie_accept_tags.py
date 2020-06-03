from django import template

from wagtail.core.models import Site

from hypha.reset_network.reset_network_cookie_accept.models import (
    ResetNetworkCookieAccept,
)

register = template.Library()


@register.inclusion_tag('reset_network_cookie_accept/message.html', takes_context=True)
def resetnetworkcookieaccept(context):
    request = context['request']
    site = Site.find_for_request(request)
    public_site = context.get('PUBLIC_SITE', site)

    return {
        'cookie_accept': ResetNetworkCookieAccept.for_site(public_site)
    }
