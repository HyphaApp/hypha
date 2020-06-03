from django import template
from wagtail.core.models import Site

from hypha.public.navigation.models import NavigationSettings

register = template.Library()


# Primary nav snippets
@register.inclusion_tag('navigation/primarynav.html', takes_context=True)
def primarynav(context):
    request = context['request']
    site_from_request = Site.find_for_request(request)
    site = context.get('PUBLIC_SITE', site_from_request)
    apply_site = context.get('APPLY_SITE', site_from_request)
    return {
        'primarynav': NavigationSettings.for_site(site).primary_navigation,
        'request': request,
        'APPLY_SITE': apply_site,
    }
