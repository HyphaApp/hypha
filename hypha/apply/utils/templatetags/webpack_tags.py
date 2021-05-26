from django import template
from django.conf import settings
from webpack_loader.templatetags import webpack_loader

register = template.Library()


@register.simple_tag
def render_bundle(bundle_name, extension=None, config='DEFAULT', attrs=''):
    """
    Render webpack bundle if enabled in settings.

    Passes the options to actual `render_bundle` template tag provided by `webpack_loader`.
    Use this instead of `webpack_loader`.
    """
    if settings.ENABLE_WEBPACK_BUNDLES:
        return webpack_loader.render_bundle(bundle_name, extension, config, attrs)
    return ''
