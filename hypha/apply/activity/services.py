from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery
from django.db.models.functions import JSONObject
from django.utils import timezone

from hypha.apply.todo.models import Task

from .models import Activity


def edit_comment(activity: Activity, message: str) -> Activity:
    """
    Edit a comment by creating a clone of the original comment with the updated message.

    Args:
        activity (Activity): The original comment activity to be edited.
        message (str): The new message to replace the original comment's message.

    Returns:
        Activity: The edited comment activity with the updated message.
    """
    if message == activity.message:
        return activity

    # Create a clone of the comment to edit
    previous = Activity.objects.get(pk=activity.pk)
    previous.pk = None
    previous.current = False
    previous.save()

    activity.previous = previous
    activity.edited = timezone.now()
    activity.message = message
    activity.current = True
    activity.save()

    return activity


def get_related_actions_for_user(obj, user):
    """Return Activity objects related to an object, esp. useful with
    ApplicationSubmission and Project.

    Args:
        obj: instance of a model class
        user: user who these actions are visible to.

    Returns:
        [`Activity`][hypha.apply.activity.models.Activity] queryset
    """
    related_query = type(obj).activities.rel.related_query_name

    return (
        Activity.actions.filter(**{related_query: obj})
        .select_related("user")
        .prefetch_related(
            "related_object",
        )
        .visible_to(user)
    )


def get_related_comments_for_user(obj, user):
    """Return comments/communications related to an object, esp. useful with
    ApplicationSubmission and Project.

    Args:
        obj: instance of a model class
        user: user who these actions are visible to.

    Returns:
        [`Activity`][hypha.apply.activity.models.Activity] queryset
    """
    related_query = type(obj).activities.rel.related_query_name

    queryset = (
        Activity.objects.filter(**{related_query: obj})
        .exclude(current=False)
        .select_related("user")
        .prefetch_related(
            "related_object",
        )
        .visible_to(user)
    )

    if user.is_apply_staff:
        assigned_to_subquery = (
            Task.objects.filter(
                related_content_type=ContentType.objects.get_for_model(Activity),
                related_object_id=OuterRef("id"),
            )
            .select_related("user")
            .values(
                json=JSONObject(
                    full_name="user__full_name", email="user__email", id="user__id"
                )
            )
        )

        queryset = queryset.annotate(assigned_to=Subquery(assigned_to_subquery))

    return queryset


def get_comment_count(obj, user):
    related_query = type(obj).activities.rel.related_query_name

    return (
        Activity.comments.filter(**{related_query: obj})
        .exclude(current=False)
        .visible_to(user)
    ).count()
