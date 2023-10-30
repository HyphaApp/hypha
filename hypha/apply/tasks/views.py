from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .models import Task
from .options import get_task_template


def add_task_to_user(code, user, related_obj):
    task = Task.objects.create(code=code, user=user, related_object=related_obj)
    return task


def add_task_to_user_group(code, user_group, related_obj):
    task = Task.objects.create(
        code=code, user_group=user_group, related_object=related_obj
    )
    return task


def remove_tasks_for_user(code, user, related_obj):
    Task.objects.filter(
        code=code,
        user=user,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).first().delete()
    return


def remove_tasks_for_user_group(code, user_group, related_obj):
    Task.objects.filter(
        code=code,
        user=user_group,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).first().delete()
    return


def get_tasks_for_user(user):
    tasks = Task.objects.filter(
        Q(user=user) | Q(user_group=user.groups.all())
    )  # :todo: exact lookup for user group
    return tasks


def render_task_templates_for_user(request, user):
    tasks = get_tasks_for_user(user)
    templates = [
        get_task_template(request, code=task.code, related_object=task.related_object)
        for task in tasks
    ]
    return templates
