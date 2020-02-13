from django import template
from opentech.reset_network.reset_network_menus.models import ResetNetworkMenusMain, ResetNetworkMenusFooter

register = template.Library()


@register.inclusion_tag('reset_network_menus/main.html', takes_context=True)
def resetnetworkmainmenu(context):

    request = context['request']

    response = {
        'APPLY_SITE': context.get('APPLY_SITE', request.site),
        'current_url': '{scheme}://{host}{path}'.format(scheme=request.scheme, host=request.get_host(), path=request.path),
        'menu_items': []
    }

    site = context.get('PUBLIC_SITE', request.site)

    if site:
        response['menu_items'] = ResetNetworkMenusMain.for_site(site).items

    return response


@register.inclusion_tag('reset_network_menus/footer.html', takes_context=True)
def resetnetworkfootermenu(context):

    request = context['request']

    response = {
        'current_url': '{scheme}://{host}{path}'.format(scheme=request.scheme, host=request.get_host(), path=request.path),
        'menu_items': []
    }

    site = context.get('PUBLIC_SITE', request.site)

    if site:
        response['menu_items'] = ResetNetworkMenusFooter.for_site(site).items

    return response
