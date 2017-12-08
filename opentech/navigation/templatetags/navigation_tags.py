from django import template

from opentech.esi import register_inclusion_tag
from opentech.navigation.models import (
    FooterNavigationSnippet,
    PrimaryNavigationSnippet,
    SecondaryNavigationSnippet
)


register = template.Library()

esi_inclusion_tag = register_inclusion_tag(register)


# Primary nav snippets
@esi_inclusion_tag('navigation/primarynav.html')
def primarynav(context):
    return {
        'primarynav': PrimaryNavigationSnippet.objects.order_by('order')[:8],
        'request': context['request'],
    }


# Secondary nav snippets
@esi_inclusion_tag('navigation/secondarynav.html')
def secondarynav(context):
    return {
        'secondarynav': SecondaryNavigationSnippet.objects.order_by('order')[:8],
        'request': context['request'],
    }


# Footer nav snippets
@esi_inclusion_tag('navigation/footernav.html')
def footernav(context):
    return {
        'footernav': FooterNavigationSnippet.objects.order_by('order')[:8],
        'request': context['request'],
    }
