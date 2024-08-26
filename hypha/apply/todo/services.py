from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from hypha.apply.activity.adapters.utils import get_users_for_groups

from .models import Task


def validate_user_uniqueness(code, user, related_obj):
    """
    code + related_object + user should be unique together.
    """
    matching_tasks = Task.objects.filter(
        code=code,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    )
    if matching_tasks.filter(user=user).exists():
        # if same task already assigned to the same user
        # raise ValidationError("Task is already assigned to the user") # :todo: add validation msg as a log msg?
        return False
    else:
        # if same task is already assigned to user's user_group
        user_group_matching_tasks = matching_tasks.annotate(
            group_count=Count("user_group")
        ).filter(group_count=len(user.groups.all()))
        for group in user.groups.all():
            user_group_matching_tasks = user_group_matching_tasks.filter(
                user_group__id=group.id
            )
        if user_group_matching_tasks.exists():
            # raise ValidationError("Task is already assigned to user's group")
            return False
        return True


def validate_user_groups_uniqueness(code, user_groups, related_obj):
    """
    code + related_object + user_group should be unique together.
    """
    matching_tasks = Task.objects.filter(
        code=code,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    )
    user_group_matching_tasks = matching_tasks.annotate(
        group_count=Count("user_group")
    ).filter(group_count=len(user_groups))
    for group in user_groups:
        user_group_matching_tasks = user_group_matching_tasks.filter(
            user_group__id=group.id
        )
    if user_group_matching_tasks.exists():
        # same task with same user_group already exists
        # :todo: add validation msg as a log msg?
        return False

    # user with exact user group already assigned for same task
    users = get_users_for_groups(
        list(user_groups), exact_match=True
    )  # users with provided user_group

    for user in users:
        if matching_tasks.filter(user=user).exists():
            Task.objects.filter(
                id=matching_tasks.id
            ).delete()  # delete those user's tasks
    return True
