import re

from bs4 import BeautifulSoup
from django.apps import apps
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import (
    Case,
    Count,
    IntegerField,
    OuterRef,
    Prefetch,
    QuerySet,
    Subquery,
    Sum,
    When,
)
from django.db.models.functions import Coalesce
from django.http import HttpRequest

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Activity, Event
from hypha.apply.funds.models.assigned_reviewers import AssignedReviewers
from hypha.apply.funds.workflow import INITIAL_STATE
from hypha.apply.review.options import DISAGREE, MAYBE
from hypha.apply.translate.translate import translate


def bulk_archive_submissions(
    submissions: QuerySet, user, request: HttpRequest
) -> QuerySet:
    """Archive submissions and generate action log.

    Args:
        submissions: queryset of submissions to archive
        user: user who is archiving the submissions
        request: django request object

    Returns:
        QuerySet of submissions that have been archived
    """
    submissions.update(is_archive=True)
    messenger(
        MESSAGES.BATCH_ARCHIVE_SUBMISSION,
        request=request,
        user=user,
        sources=submissions,
    )
    return submissions


def bulk_delete_submissions(
    submissions: QuerySet, user, request: HttpRequest
) -> QuerySet:
    """Permanently deletes submissions and generate action log.

    Args:
        submissions: queryset of submissions to archive
        user: user who is archiving the submissions
        request: django request object

    Returns:
        QuerySet of submissions that have been archived
    """
    # delete NEW_SUBMISSION events for all submissions
    submission_ids = submissions.values_list("id", flat=True)
    Event.objects.filter(
        type=MESSAGES.NEW_SUBMISSION, object_id__in=submission_ids
    ).delete()
    # delete submissions
    submissions.delete()
    messenger(
        MESSAGES.BATCH_DELETE_SUBMISSION,
        request=request,
        user=user,
        sources=submissions,
    )
    return submissions


def bulk_update_lead(
    submissions: QuerySet, user, request: HttpRequest, lead
) -> QuerySet:
    """Update lead for submissions and generate action log.

    Args:
        submissions: queryset of submissions to update
        user: user who is changing the lead
        request: django request object
        lead: user who is the new lead

    Returns:
        QuerySet of submissions that have been changed
    """
    submissions = submissions.exclude(lead=lead)
    submissions.update(lead=lead)

    messenger(
        MESSAGES.BATCH_UPDATE_LEAD,
        request=request,
        user=user,
        sources=submissions,
        new_lead=lead,
    )
    return submissions


def bulk_update_reviewers(
    submissions: QuerySet,
    user,
    request: HttpRequest,
    assigned_roles: dict,
    external_reviewers=None,
) -> QuerySet:
    """Update reviewer for submissions and generate action log.

    Args:
        submissions: queryset of submissions to update
        user: user who is changing the reviewer
        request: django request object
        assigned_roles: roles and reviewers to assign against them
        reviewer: user who is the new reviewer

    Returns:
        QuerySet of submissions that have been changed
    """
    for role, reviewer in assigned_roles.items():
        if reviewer:
            AssignedReviewers.objects.update_role(role, reviewer, *submissions)

    for submission in submissions:
        AssignedReviewers.objects.bulk_create_reviewers(
            external_reviewers or [],
            submission,
        )

    messenger(
        MESSAGES.BATCH_REVIEWERS_UPDATED,
        request=request,
        user=user,
        sources=submissions,
        added=[[role, reviewer] for role, reviewer in assigned_roles.items()],
    )

    for submission in submissions:
        set_status_after_reviewers_assigned(
            submission, updated_by=user, request=request
        )

    return submissions


def annotate_comments_count(submissions: QuerySet, user) -> QuerySet:
    comments = Activity.comments.filter(submission=OuterRef("id")).visible_to(user)
    return submissions.annotate(
        comment_count=Coalesce(
            Subquery(
                comments.values("submission")
                .order_by()
                .annotate(count=Count("pk"))
                .values("count"),
                output_field=IntegerField(),
            ),
            0,
        ),
    )


def set_status_after_reviewers_assigned(submission, updated_by, request) -> None:
    if not settings.TRANSITION_AFTER_ASSIGNED:
        return None

    # Check if all internal reviewers have been selected.
    if submission.has_all_reviewer_roles_assigned:
        # Automatic workflow actions.
        action = None
        if submission.status == INITIAL_STATE:
            # Automatically transition the application to "Internal review".
            action = submission.workflow.stepped_phases[2][0].name
        elif submission.status == "proposal_discussion":
            # Automatically transition the proposal to "Internal review".
            action = "proposal_internal_review"

        # If action is set run perform_transition().
        if action:
            try:
                submission.perform_transition(
                    action,
                    updated_by,
                    request=request,
                    notify=False,
                )
            except (PermissionDenied, KeyError):
                pass


def annotate_review_recommendation_and_count(submissions: QuerySet) -> QuerySet:
    Review = apps.get_model("review", "Review")
    ReviewOpinion = apps.get_model("review", "ReviewOpinion")
    AssignedReviewers = apps.get_model("funds", "AssignedReviewers")

    reviews = Review.objects.filter(submission=OuterRef("id"))
    opinions = ReviewOpinion.objects.filter(review__submission=OuterRef("id"))
    reviewers = AssignedReviewers.objects.filter(submission=OuterRef("id"))

    submissions = submissions.annotate(
        review_count=Subquery(
            reviewers.values("submission").annotate(count=Count("pk")).values("count"),
            output_field=IntegerField(),
        ),
        review_staff_count=Subquery(
            reviewers.staff()
            .values("submission")
            .annotate(count=Count("pk"))
            .values("count"),
            output_field=IntegerField(),
        ),
        review_submitted_count=Subquery(
            reviewers.reviewed()
            .values("submission")
            .annotate(count=Count("pk", distinct=True))
            .values("count"),
            output_field=IntegerField(),
        ),
        opinion_disagree=Subquery(
            opinions.filter(opinion=DISAGREE)
            .values("review__submission")
            .annotate(count=Count("*"))
            .values("count")[:1],
            output_field=IntegerField(),
        ),
        review_recommendation=Case(
            When(opinion_disagree__gt=0, then=MAYBE),
            default=Subquery(
                reviews.submitted()
                .values("submission")
                .annotate(
                    calc_recommendation=Sum("recommendation") / Count("recommendation"),
                )
                .values("calc_recommendation"),
                output_field=IntegerField(),
            ),
        ),
    ).prefetch_related(
        Prefetch(
            "assigned",
            queryset=AssignedReviewers.objects.reviewed()
            .review_order()
            .select_related(
                "reviewer",
            )
            .prefetch_related(
                Prefetch(
                    "review__opinions",
                    queryset=ReviewOpinion.objects.select_related("author"),
                ),
            ),
            to_attr="has_reviewed",
        ),
        Prefetch(
            "assigned",
            queryset=AssignedReviewers.objects.not_reviewed().staff(),
            to_attr="hasnt_reviewed",
        ),
    )
    return submissions


def translate_submission_form_data(
    submission, from_code: str, to_code: str
) -> dict | None:
    """Translate the content of an application's `form_data`

    Args:
        submission: the submission to translate
        from_code: the ISO 639 code of the original language
        to_code: the ISO 639 code of the language to translate to

    Returns:
        The `form_data` with values translated if succcessful, otherwise `None`

    Raises:
        ValueError if an invalid `from_code` or `to_code` is requested

    """

    translated_form_data = {}

    form_data = submission.live_revision.form_data

    for key in form_data:
        # Only translate content fields or the title - don't with name, email, etc.
        if key == "title":
            translated_form_data[key] = translate(form_data[key], from_code, to_code)
        elif key == "title" or re.match(
            r"([a-z]|\d){8}(-([a-z]|\d){4}){3}-([a-z]|\d){12}", key
        ):
            field_html = BeautifulSoup(form_data[key], "html.parser")
            if field_html.find():
                text_fields = [
                    field
                    for field in field_html.findAll(["span", "p", "strong", "td"])
                    if field.find(string=True, recursive=False)
                ]
                for field in text_fields:
                    if field.string:
                        field["lang"] = to_code
                        field.string = translate(field.string, from_code, to_code)

                translated_form_data[key] = str(field_html)
            else:
                translated_form_data[key] = translate(
                    form_data[key], from_code, to_code
                )
        else:
            translated_form_data[key] = form_data[key]

    return translated_form_data
