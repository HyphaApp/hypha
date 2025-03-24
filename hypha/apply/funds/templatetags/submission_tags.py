import re

from django import template
from django.db.models import Q
from django.utils.safestring import mark_safe

from hypha.apply.funds.models import ApplicationSubmission

register = template.Library()


@register.filter
def submission_links(value):
    # regex to find #id in a string, which id can be alphanumeric, underscore, hyphen
    matches = re.findall(r"(?<![\w\&])\#([\w-]+)(?!\w)", value)
    links = {}
    if matches:
        numeric_ids = filter(str.isdigit, matches)
        qs = ApplicationSubmission.objects.filter(
            Q(id__in=numeric_ids) | Q(public_id__in=matches)
        )
        for submission in qs:
            links[f"#{submission.application_id}"] = (
                f'<a href="{submission.get_absolute_url()}">{submission.title_text_display}</a>'
            )

    if links:
        for sid, link in links.items():
            value = re.sub(rf"(?<!\w){sid}(?!\w)", link, value)

    return mark_safe(value)
