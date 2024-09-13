import re

from django import template
from django.db.models import Q
from django.utils.safestring import mark_safe

from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.funds.permissions import has_permission

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
            links[rf"\#{submission.public_id or submission.id}"] = (
                f'<a href="{submission.get_absolute_url()}">{submission.title} <span class="text-gray-400">#{submission.public_id or submission.id}</span></a>'
            )

    if links:
        for sid, link in links.items():
            value = re.sub(rf"(?<!\w){sid}(?!\w)", link, value)

    return mark_safe(value)


@register.filter
def doc_title(submission) -> str:
    id = submission.public_id if submission.public_id else object.id
    return f"#{id}: { submission.title }"


@register.simple_tag
def user_can_delete_submission(submission, user):
    permission, _ = has_permission(
        "submission_delete",
        user=user,
        object=submission,
        raise_exception=False,
    )
    return permission
