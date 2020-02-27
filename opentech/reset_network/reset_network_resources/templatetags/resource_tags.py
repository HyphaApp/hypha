from django import template
from django.template.defaultfilters import filesizeformat


register = template.Library()


@register.filter
def resilientfilesizeformat(value):

    try:
        filesizeformat(value.asset.file.size)
    except Exception:
        return 'Download'
