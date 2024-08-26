from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View
from django_htmx.http import trigger_client_event

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.users.decorators import staff_required

from .models import Task
from .options import get_task_template
from .services import validate_user_groups_uniqueness, validate_user_uniqueness


@method_decorator(staff_required, name="dispatch")
class TodoListView(ListView):
    model = Task
    template_name = "todo/todolist_dropdown.html"

    def get_queryset(self):
        tasks = render_task_templates_for_user(self.request, self.request.user)
        return tasks

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["my_tasks"] = {"data": self.get_queryset()}
        return ctx


@method_decorator(staff_required, name="dispatch")
class TaskRemovalView(View):
    def dispatch(self, request, *args, **kwargs):
        self.task = get_object_or_404(Task, id=self.kwargs.get("pk"))
        if self.task.user == request.user or set(self.task.user_group.all()) == set(
            request.user.groups.all()
        ):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("You can remove the tasks that are assigned to you.")

    def delete(self, *args, **kwargs):
        source = self.task.related_object
        from hypha.apply.activity.models import Activity
        from hypha.apply.determinations.models import Determination
        from hypha.apply.projects.models import Invoice
        from hypha.apply.review.models import Review

        if isinstance(self.task.related_object, Invoice):
            source = self.task.related_object.project
        elif isinstance(self.task.related_object, Determination) or isinstance(
            self.task.related_object, Review
        ):
            source = self.task.related_object.submission
        elif isinstance(self.task.related_object, Activity):
            source = self.task.related_object.source
        messenger(
            MESSAGES.REMOVE_TASK,
            user=self.request.user,
            request=self.request,
            source=source,
            related=self.task,
        )
        self.task.delete()
        tasks = render_task_templates_for_user(self.request, self.request.user)
        response = render(
            self.request,
            "dashboard/includes/my-tasks.html",
            context={"my_tasks": {"data": tasks}},
        )
        trigger_client_event(response, "taskListUpdated", {})
        return response


def add_task_to_user(code, user, related_obj):
    """
    Add task for a user
    input:
        code: TASKS_CODE_CHOICES.keys()
        user: User object
        related_obj: Object - Submission, Project, Invoice, Report
    output: task - Task object / None in case of no creation
    """
    user_uniqueness = validate_user_uniqueness(
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


def remove_tasks_of_related_obj_for_specific_code(code, related_obj):
    """
    Remove all tasks of a related object with the provide code irrespective to their users
    input:
        code: TASKS_CODE_CHOICES.keys()
        related_obj: Object - Submission, Project, Invoice, Report
    """
    Task.objects.filter(
        code=code,
        related_content_type=ContentType.objects.get_for_model(related_obj).id,
        related_object_id=related_obj.id,
    ).delete()
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
    templates = [get_task_template(request, task=task) for task in tasks]

    return list(filter(None, templates))
