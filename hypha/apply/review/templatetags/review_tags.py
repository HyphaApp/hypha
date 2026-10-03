from django import template
from django.conf import settings
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
def reviews_score(reviewers):
    """The combined score of the submitted reviews, for the reviews sidebar.

    Either the total of every review's total score or the average of their
    average scores, depending on ``REVIEW_SCORE_SHOW_TOTAL``.
    """
    if not reviewers:
        return ""

    # `has_review` is annotated by AssignedReviewersQuerySet.review_order() and
    # is 1 when the reviewer has no review, so `not has_review` means they do.
    reviews = [
        reviewer.review
        for reviewer in reviewers
        if not reviewer.has_review and not reviewer.review.is_draft
    ]

    if settings.REVIEW_SCORE_SHOW_TOTAL:
        totals = [
            review.total_score for review in reviews if review.total_score is not None
        ]
        if totals:
            return _("Total score: {total}").format(total="{:.0f}".format(sum(totals)))
        return ""

    scores = [review.score for review in reviews if review.score != NA]
    if scores:
        return _("Avg. score: {average}").format(
            average=round(sum(scores) / len(scores), 1)
        )
    return ""
