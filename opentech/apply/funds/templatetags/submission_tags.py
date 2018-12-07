import re

from django import template
from django.utils.safestring import mark_safe

from opentech.apply.funds.models import ApplicationSubmission

register = template.Library()


@register.filter
def submission_links(value):
    # Match tags in the format #123 that is not preceeded and/or followed by a word character.
    matches = re.findall('(?<!\w)\#(\d+)(?!\w)', value)
    links = {}
    if matches:
        for submission in ApplicationSubmission.objects.filter(id__in=matches):
            links[f'\#{submission.id}'] = f'<a href="{submission.get_absolute_url()}">{submission.title} <span class="mid-grey-text">#{submission.id}</span></a>'

    if links:
        for sid, link in links.items():
            value = re.sub(f'(?<!\w){sid}(?!\w)', link, value)

    return mark_safe(value)
