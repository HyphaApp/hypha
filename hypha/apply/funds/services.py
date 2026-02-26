from django.apps import apps
from django.conf import settings
from django.contrib import messages
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
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Activity, Event
from hypha.apply.funds.models.assigned_reviewers import AssignedReviewers
from hypha.apply.funds.workflows import INITIAL_STATE
from hypha.apply.funds.workflows.constants import DRAFT_STATE
from hypha.apply.review.options import DISAGREE, MAYBE


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
    # update submissions
    submissions.update(is_archive=True)

    messages.success(
        request, _("{number} submissions archived.").format(number=len(submissions))
    )

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
        submissions: queryset of submissions to delete
        user: user who is deleting the submissions
        request: django request object

    Returns:
        QuerySet of submissions that have been archived
    """
    # delete NEW_SUBMISSION events for all submissions
    submission_ids = submissions.values_list("id", flat=True)
    Event.objects.filter(
        type=MESSAGES.NEW_SUBMISSION, object_id__in=submission_ids
    ).delete()

    messages.success(
        request, _("{number} submissions deleted.").format(number=len(submissions))
    )

    messenger(
        MESSAGES.BATCH_DELETE_SUBMISSION,
        request=request,
        user=user,
        sources=submissions,
    )
    # delete submissions
    submissions.delete()
    return submissions


def bulk_covert_to_skeleton_submissions(
    submissions: QuerySet, user, request: HttpRequest
) -> QuerySet:
    """Converts submissions to skeleton submissions, deletes draft submissions and generates action log.

    Args:
        submissions: queryset of submissions to convert to skeleton applications
        user: user who is archiving the submissions
        request: django request object

    Returns:
        QuerySet of submissions that have been archived
    """
    ApplicationSubmission = apps.get_model("funds", "ApplicationSubmission")
    ApplicationSubmissionSkeleton = apps.get_model(
        "funds", "ApplicationSubmissionSkeleton"
    )

    # delete NEW_SUBMISSION events for all submissions
    submission_dict_list = submissions.values(
        "id", "form_data", "page_id", "round_id", "status", "submit_time"
    )

    submission_ids = [x["id"] for x in submission_dict_list]

    Event.objects.filter(
        type=MESSAGES.NEW_SUBMISSION, object_id__in=submission_ids
    ).delete()

    for submission_dict in submission_dict_list:
        if submission_dict["status"] != DRAFT_STATE:
            ApplicationSubmissionSkeleton.from_dict(submission_dict)

    # delete submissions
    submissions = ApplicationSubmission.objects.filter(id__in=submission_ids)
    submissions.delete()

    messages.success(
        request,
        ngettext(
            "{sub_number} submission anonymized",
            "{sub_number} submissions anonymized",
            len(submission_ids),
        ).format(sub_number=len(submission_ids)),
    )

    messenger(
        MESSAGES.BATCH_SKELETON_SUBMISSION,
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

    base_message = _("Lead set to {lead} on ").format(lead=lead)
    submissions_text = [submission.title_text_display for submission in submissions]
    messages.success(request, base_message + ", ".join(submissions_text))

    messenger(
        MESSAGES.BATCH_UPDATE_LEAD,
        request=request,
        user=user,
        sources=submissions,
        new_lead=lead,
    )

    # update submissions
    submissions.update(lead=lead)
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

    added = [[role, reviewer] for role, reviewer in assigned_roles.items()]
    if added:
        reviewers_text = ", ".join(
            [
                _("{user} as {name}").format(user=str(user), name=role.name)
                for role, user in added
                if user
            ]
        )
    else:
        reviewers_text = ", ".join([str(user) for user in external_reviewers if user])

    base_message = _("Batch reviewers updated: {reviewers_text} on ").format(
        reviewers_text=reviewers_text
    )
    submissions_text = [submission.title_text_display for submission in submissions]
    messages.success(request, base_message + ", ".join(submissions_text))

    messenger(
        MESSAGES.BATCH_REVIEWERS_UPDATED,
        request=request,
        user=user,
        sources=submissions,
        added=added,
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
