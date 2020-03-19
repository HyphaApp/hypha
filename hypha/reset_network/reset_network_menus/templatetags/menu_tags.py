from django import template
from hypha.reset_network.reset_network_menus.models import ResetNetworkMenusMain, ResetNetworkMenusFooter

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
        menu_items = ResetNetworkMenusMain.for_site(site).items
        menu_items = [i for i in menu_items if i.value['page'] and i.value['page'].live]
        response['menu_items'] = menu_items

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
        menu_items = ResetNetworkMenusFooter.for_site(site).items
        menu_items = [i for i in menu_items if i.value['page'] and i.value['page'].live]
        response['menu_items'] = menu_items

    return response
