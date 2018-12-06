import re

from django import template
from django.utils.safestring import mark_safe

from opentech.apply.funds.models import ApplicationSubmission

register = template.Library()


@register.filter
def submission_links(value):
    regex = re.compile('[^\w]\#(\d+)[^\w]')
    links = {}
    for match in regex.finditer(value):
        try:
            submission = ApplicationSubmission.objects.get(id=match[1])
        except ApplicationSubmission.DoesNotExist:
            pass
        else:
            links[f'#{submission.id}'] = f'<a href="{submission.get_absolute_url()}">{submission.title} <span class="mid-grey-text">#{submission.id}</span></a>'

    if links:
        for sid, link in links.items():
            value = value.replace(sid, link)

    return mark_safe(value)
