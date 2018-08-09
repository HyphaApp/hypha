from django import template

from opentech.public.navigation.models import NavigationSettings


register = template.Library()


# Primary nav snippets
@register.inclusion_tag('navigation/primarynav.html', takes_context=True)
def primarynav(context):
    request = context['request']
    site = context.get('PUBLIC_SITE', request.site)
    return {
        'primarynav': NavigationSettings.for_site(site).primary_navigation,
        'request': request,
    }
