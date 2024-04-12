from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from .models import Task
from .options import get_task_template
from .services import validate_user_groups_uniqueness, validate_user_uniquness


def add_task_to_user(code, user, related_obj):
    """
    Add task for a user
    input:
        code: TASKS_CODE_CHOICES.keys()
        user: User object
        related_obj: Object - Submission, Project, Invoice, Report
    output: task - Task object / None in case of no creation
    """
    user_uniqueness = validate_user_uniquness(
        code=code, user=user, related_obj=related_obj
    )
    if user_uniqueness:
        task = Task.objects.create(code=code, user=user, related_object=related_obj)
        return task
    return None


def add_task_to_user_group(code, user_group, related_obj):
    """
    Add task for user_groups
    input:
        code: TASKS_CODE_CHOICES.keys()
        user_group: Queryset - Group objects
        related_obj: Object - Submission, Project, Invoice, Report
    output: task - Task object / None in case of no creation
    """
    user_groups_uniqueness = validate_user_groups_uniqueness(
        code=code, user_groups=user_group, related_obj=related_obj
    )
    if user_groups_uniqueness:
        task = Task.objects.create(code=code, related_object=related_obj)
        groups = [Group.objects.filter(id=group.id).first() for group in user_group]
        task.user_group.add(*groups)
        return task
    return None


def remove_tasks_for_user(code, user, related_obj):
    """
    Remove task for a user
    input:
        code: TASKS_CODE_CHOICES.keys()
        user: User object
        related_obj: Object - Submission, Project, Invoice, Report
    output: None
    """
    task = Task.objects.filter(
        code=code,
        user=user,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).first()
    if task:
        task.delete()
    return None


def remove_tasks_for_user_group(code, user_group, related_obj):
    """
    Remove task for user_groups
    input:
        code: TASKS_CODE_CHOICES.keys()
        user_group: Queryset - Group objects
        related_obj: Object - Submission, Project, Invoice, Report
    output: None
    """
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


def remove_tasks_of_related_obj(related_obj):
    """
    Remove all tasks of a related object irrespective of their code and users
    input:
        related_obj: Object - Submission, Project, Invoice, Report
    """
    Task.objects.filter(
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).delete()
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

    return list(filter(None, templates))
