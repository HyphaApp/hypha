from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def update_urlparams(context, param, value):
    url = context.get('request').get_full_path()
    parsed_url = urlparse(url)
    query_params = dict(parse_qs(parsed_url.query))
    query_params.update({str(param): str(value)})
    url = urlunparse(parsed_url._replace(query=urlencode(query=query_params, doseq=True)))
    return url


@register.simple_tag(takes_context=True)
def get_url_param(context, param):
    url = context.get('request').get_full_path()
    parsed_url = urlparse(url)
    captured_value = parse_qs(parsed_url.query)

    if captured_value and param in captured_value.keys():
        return captured_value[param][0]
    return None
