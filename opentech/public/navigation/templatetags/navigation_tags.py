from django import template

from opentech.public.esi import register_inclusion_tag
from opentech.public.navigation.models import NavigationSettings


register = template.Library()

esi_inclusion_tag = register_inclusion_tag(register)


# Primary nav snippets
@esi_inclusion_tag('navigation/primarynav.html')
def primarynav(context):
    request = context['request']
    site = context.get('PUBLIC_SITE', request.site)
    apply_site = context.get('APPLY_SITE', request.site)
    return {
        'primarynav': NavigationSettings.for_site(site).primary_navigation,
        'request': request,
        'APPLY_SITE': apply_site,
    }
