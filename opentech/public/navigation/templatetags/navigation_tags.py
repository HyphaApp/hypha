from django import template

from opentech.public.esi import register_inclusion_tag
from opentech.public.navigation.models import NavigationSettings


register = template.Library()

esi_inclusion_tag = register_inclusion_tag(register)


# Primary nav snippets
@esi_inclusion_tag('navigation/primarynav.html')
def primarynav(context):
    request = context['request']
    return {
        'primarynav': NavigationSettings.for_site(request.site).primary_navigation,
        'request': request,
    }


# Secondary nav snippets
@esi_inclusion_tag('navigation/secondarynav.html')
def secondarynav(context):
    request = context['request']
    return {
        'secondarynav': NavigationSettings.for_site(request.site).secondary_navigation,
        'request': request,
    }


# Footer nav snippets
@esi_inclusion_tag('navigation/footernav.html')
def footernav(context):
    request = context['request']
    return {
        'footernav': NavigationSettings.for_site(request.site).footer_navigation,
        'request': request,
    }


# Footer nav snippets
@esi_inclusion_tag('navigation/sidebar.html')
def sidebar(context):
    return {
        'children': context['page'].get_children().live().public().in_menu(),
        'request': context['request'],
    }


# Footer nav snippets
@esi_inclusion_tag('navigation/footerlinks.html')
def footerlinks(context):
    request = context['request']
    return {
        'footerlinks': NavigationSettings.for_site(request.site).footer_links,
        'request': request,
    }
