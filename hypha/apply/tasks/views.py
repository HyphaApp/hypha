from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from hypha.apply.users.models import Group

from .models import Task
from .options import get_task_template


def add_task_to_user(code, user, related_obj):
    task = Task.objects.create(code=code, user=user, related_object=related_obj)
    return task


def add_task_to_user_group(code, user_group, related_obj):
    task = Task.objects.create(code=code, related_object=related_obj)
    groups = [Group.objects.filter(id=group.id).first() for group in user_group]
    task.user_group.add(*groups)
    return task


def remove_tasks_for_user(code, user, related_obj):
    Task.objects.filter(
        code=code,
        user=user,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).first().delete()
    return None


def remove_tasks_for_user_group(code, user_group, related_obj):
    matching_tasks = Task.objects.filter(
        code=code,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    )
    user_group_matching_tasks = matching_tasks.annotate(
        group_count=Count("user_group")
    ).filter(group_count=len(user_group.all()))
    for group in user_group.all():
        user_group_matching_tasks = user_group_matching_tasks.filter(
            user_group__id=group.id
        )
    if user_group_matching_tasks.exists():
        user_group_matching_tasks.delete()
    return None


def get_tasks_for_user(user):
    user_tasks = Task.objects.filter(user=user).annotate(
        group_count=Count("user_group")
    )
    user_group_tasks = Task.objects.annotate(group_count=Count("user_group")).filter(
        group_count=len(user.groups.all())
    )
    for group in user.groups.all():
        user_group_tasks = user_group_tasks.filter(user_group__id=group.id)

    return user_tasks.union(user_group_tasks)


def render_task_templates_for_user(request, user):
    """
    input: request (HttpRequest)
    input: user   (User object)

    output: [{
                 "text":"",
                 "icon":"",
                 "url":"",
                 "type":"",
             },
            ]
    """
    tasks = get_tasks_for_user(user)
    templates = [
        get_task_template(request, code=task.code, related_obj=task.related_object)
        for task in tasks
    ]
    return templates
