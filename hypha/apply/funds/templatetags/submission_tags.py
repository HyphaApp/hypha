import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django import template
from django.utils.safestring import mark_safe

from hypha.apply.funds.models import ApplicationSubmission

register = template.Library()


@register.filter
def submission_links(value):
    # Match tags in the format #123 that is not preceeded and/or followed by a word character.
    matches = re.findall(r'(?<![\w\&])\#(\d+)(?!\w)', value)
    links = {}
    if matches:
        for submission in ApplicationSubmission.objects.filter(id__in=matches):
            links[fr'\#{submission.id}'] = f'<a href="{submission.get_absolute_url()}">{submission.title} <span class="mid-grey-text">#{submission.id}</span></a>'

    if links:
        for sid, link in links.items():
            value = re.sub(fr'(?<!\w){sid}(?!\w)', link, value)

    return mark_safe(value)


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


@register.simple_tag
def can_screen(submission):
    if submission.is_archive:
        return False
    return True
