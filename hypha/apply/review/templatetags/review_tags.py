from django import template
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from ..models import MAYBE, NO, YES
from ..options import NA

register = template.Library()


@register.filter()
def traffic_light(value):
    mapping = {
        YES: {
            "label": _("Overall recommendation: Yes"),
            "class": "triangle-up text-success",
        },
        MAYBE: {
            "label": _("Overall recommendation: Maybe"),
            "class": "circle text-warning",
        },
        NO: {
            "label": _("Overall recommendation: No"),
            "class": "triangle-down text-error",
        },
    }

    try:
        html = """
            <div class="flex items-center">
                <span class="size-3 {class}" aria-hidden=true></span>
                <span class="sr-only">{label}</span>
            </div>
        """
        return format_html(html, **mapping[value])
    except KeyError:
        return ""


@register.filter
def can_review(user, submission):
    return submission.can_review(user)


@register.filter
def has_draft(user, submission):
    return (
        submission.can_review(user)
        and submission.assigned.draft_reviewed().filter(reviewer=user).exists()
    )


@register.filter
def average_review_score(reviewers):
    if reviewers:
        scores = [
            reviewer.review.score
            for reviewer in reviewers
            if not reviewer.has_review
            and not reviewer.review.is_draft
            and not reviewer.review.score == NA
        ]
        if len(scores) > 0:
            return _("Avg. score: {average}").format(
                average=round(sum(scores) / len(scores), 1)
            )
    return ""
