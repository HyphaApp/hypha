from django import template
from django.template.defaultfilters import filesizeformat


register = template.Library()


@register.filter
def resilientfilesizeformat(value):

    try:
        size = filesizeformat(value.asset.file.size)
        if size:
            return size
        else:
            return 'Download'
    except Exception:
        return 'Download'
