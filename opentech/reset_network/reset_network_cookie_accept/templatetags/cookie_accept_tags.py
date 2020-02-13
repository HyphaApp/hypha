from django import template
from opentech.reset_network.reset_network_cookie_accept.models import ResetNetworkCookieAccept

register = template.Library()


@register.inclusion_tag('reset_network_cookie_accept/message.html', takes_context=True)
def resetnetworkcookieaccept(context):
    request = context['request']

    site = context.get('PUBLIC_SITE', request.site)

    return {
        'cookie_accept': ResetNetworkCookieAccept.for_site(site)
    }
