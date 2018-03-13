from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string


ESI_REGISTRY = {}


def register_inclusion_tag(register):
    def esi_inclusion_tag(template):
        def dec(func):
            name = func.__name__

            if name in ESI_REGISTRY:
                raise Exception("There's already an esi_inclusion_tag called '%s'" % name)

            ESI_REGISTRY[name] = {
                'get_context': func,
                'template': template
            }

            @register.simple_tag(name=name, takes_context=True)
            def tag_func(context):
                if settings.ESI_ENABLED:
                    root_url = context['request'].site.root_url
                    # Note that ESI has been used on the request object
                    # This allows the ESI middleware to know when to set the X-ESI header on the response
                    context['request']._esi_include_used = True
                    return '<esi:include src="%s/esi/%s/" />' % (root_url, name)
                else:
                    return render_to_string(template, func(context))

            return tag_func
        return dec
    return esi_inclusion_tag


def purge_esi():
    from opentech.public.utils.cache import purge_cache_on_all_sites

    for name in ESI_REGISTRY:
        # TODO: might need a separate domain for ESI and call wagtail.contrib.frontend_cache.utils.purge_url_from_cache
        purge_cache_on_all_sites(reverse('esi', args=[name]))
