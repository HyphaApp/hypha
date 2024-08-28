from django.contrib.contenttypes.models import ContentType
from django.db.models import OuterRef, Subquery

from hypha.apply.todo.models import Task

from .models import Activity


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
        Activity.comments.filter(**{related_query: obj})
        .select_related("user")
        .prefetch_related(
            "related_object",
        )
        .visible_to(user)
    )

    if user.is_apply_staff:
        assigned_to_subquery = Task.objects.filter(
            related_content_type=ContentType.objects.get_for_model(Activity),
            related_object_id=OuterRef("id"),
        ).values("user__full_name")

        queryset = queryset.annotate(assigned_to=Subquery(assigned_to_subquery))

    return queryset
