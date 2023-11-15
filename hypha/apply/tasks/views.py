from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from .models import Task
from .options import get_task_template


def add_task_to_user(code, user, related_obj):
    task = Task.objects.create(code=code, user=user, related_object=related_obj)
    return task


def add_task_to_user_group(code, user_group, related_obj):
    # :todo: fix direct assignment of user_group
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
    # :todo: fix direct assignment for user group(many to many)
    Task.objects.filter(
        code=code,
        user=user_group,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).first().delete()
    return


def get_tasks_for_user(user):
    user_tasks = Task.objects.filter(user=user)
    user_group_tasks = Task.objects.annotate(group_count=Count("user_group")).filter(
        group_count=len(user.groups.all())
    )
    for group in user.groups.all():
        user_group_tasks = user_group_tasks.filter(user_group__id=group.id)

    # todo: test union for merging user and user_group querysets

    return user_tasks


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
