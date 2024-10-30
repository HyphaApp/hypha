import re

from bs4 import BeautifulSoup, element
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
from hypha.apply.translate import translate


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


def translate_submission_form_data(submission, from_code: str, to_code: str) -> dict:
    """Translate the content of an application's live revision `form_data`.
    Will parse fields that contain both plaintext & HTML, extracting & replacing strings.

    NOTE: Mixed formatting like `<p>Hey from <strong>Hypha</strong></p>` will result in a
    string that is stripped of text formatting (untranslated: `<p>Hey from Hypha</p>`). On
    the other hand, unmixed strings like `<p><strong>Hey from Hypha</strong></p>` will be
    replaced within formatting tags.

    Args:
        submission: the submission to translate
        from_code: the ISO 639 code of the original language
        to_code: the ISO 639 code of the language to translate to

    Returns:
        The `form_data` with values translated (including nested HTML strings)

    Raises:
        ValueError if an invalid `from_code` or `to_code` is requested
    """
    form_data: dict = submission.live_revision.form_data

    translated_form_data = form_data.copy()

    # Only translate content fields or the title - don't with name, email, etc.
    translated_form_data["title"] = translate.translate(
        form_data["title"], from_code, to_code
    )

    # RegEx to match wagtail's generated field UIDs - ie. "97c51cea-ab47-4a64-a64a-15d893788ef2"
    uid_regex = re.compile(r"([a-z]|\d){8}(-([a-z]|\d){4}){3}-([a-z]|\d){12}")
    fields_to_translate = [
        key
        for key in form_data
        if uid_regex.match(key) and isinstance(form_data[key], str)
    ]

    for key in fields_to_translate:
        field_html = BeautifulSoup(form_data[key], "html.parser")
        if field_html.find():  # Check if BS detected any HTML
            for field in field_html.find_all(has_valid_str):
                # Removes formatting if mixed into the tag to prioritize context in translation
                # ie. `<p>Hey <strong>y'all</strong></p>` -> `<p>Hey y'all</p>` (but translated)
                to_translate = field.string if field.string else field.text
                field.clear()
                field.string = translate.translate(to_translate, from_code, to_code)

            translated_form_data[key] = str(field_html)
        # Ensure the field value isn't empty & translate as is
        elif form_data[key].strip():
            translated_form_data[key] = translate.translate(
                form_data[key], from_code, to_code
            )

    return translated_form_data


def has_valid_str(tag: element.Tag) -> bool:
    """Checks that an Tag contains a valid text element and/or string.

    Args:
        tag: a `bs4.element.Tag`
    Returns:
        bool: True if has a valid string that isn't whitespace or `-`
    """
    text_elem = tag.name in ["span", "p", "strong", "em", "td", "a"]

    try:
        # try block logic handles elements that have text directly in them
        # ie. `<p>test</p>` or `<em>yeet!</em>` would return true as string values would be contained in tag.string
        ret = bool(
            text_elem
            and tag.find(string=True, recursive=False)
            and tag.string.strip(" -\n")
        )
        return ret
    except AttributeError:
        # except block logic handles embedded tag strings where tag.string == None but the specified tag DOES contain a string
        # ie. `<p>Hypha is <strong>cool</strong></p>` contains the string "Hypha is" but due to the strong tag being mixed in will
        # have None for the tag.string value.
        # tags like `<p> <em>Hypha rocks</em> </p>` will return false as the <p> tag contains no valid strings, it's child does.
        tag_contents = "".join(tag.find_all(string=True, recursive=False))
        ret = bool(tag.text and tag.text.strip() and tag_contents.strip())
        return ret
