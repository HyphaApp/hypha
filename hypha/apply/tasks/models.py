from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import ValidationError
from django.db import models

from hypha.apply.activity.adapters.utils import get_users_for_groups
from hypha.apply.users.models import Group, User

from .options import TASKS_CODE_CHOICES


class Task(models.Model):
    code = models.CharField(choices=TASKS_CODE_CHOICES, max_length=50)
    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE, related_name="task"
    )
    user_group = models.ManyToManyField(
        Group,
        related_name="task",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    related_content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="task_related",
    )
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object = GenericForeignKey("related_content_type", "related_object_id")

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        if (not self.user and not self.user_group) or (self.user and self.user_group):
            raise ValidationError(
                "Task should be assigned either to a user or a user group"
            )

    def validate_unique(self, exclude=None):
        """
        code + related_object + user/user_group should be unique together.
        """
        # todo: no need to raise ValidationError in this method just abort the save.
        matching_tasks = Task.objects.filter(
            code=self.code,
            related_content_type=ContentType.objects.get_for_model(
                self.related_object
            ).id,
            related_object_id=self.related_object.id,
        )
        if self.user:
            if matching_tasks.filter(user=self.user).exists():
                # if same task already assigned to the same user
                raise ValidationError("Task is already assigned to the user")
            else:
                # if same task is already assigned to user's user_group
                user_group_matching_tasks = matching_tasks.annotate(
                    group_count=models.Count("user_group")
                ).filter(group_count=len(self.user.groups.all()))
                for group in self.user.groups.all():
                    user_group_matching_tasks = user_group_matching_tasks.filter(
                        user_group__id=group.id
                    )
                if user_group_matching_tasks.exists():
                    raise ValidationError("Task is already assigned to user's group")
        if self.pk is not None and self.user_group:
            # if same task is already assigned to same user_group
            user_group_matching_tasks = matching_tasks.annotate(
                group_count=models.Count("user_group")
            ).filter(group_count=len(self.user_group.all()))
            for group in self.user_group.all():
                user_group_matching_tasks = user_group_matching_tasks.filter(
                    user_group__id=group.id
                )
            if user_group_matching_tasks.exists():
                raise ValidationError("Task is already assigned to the user group")

            # user with exact user group already assigned for same task
            users = get_users_for_groups(
                list(self.user_group.all()), exact_match=True
            )  # users with provided user_group

            for user in users:
                if matching_tasks.filter(user=user).exists():
                    Task.objects.filter(
                        id=matching_tasks.id
                    ).delete()  # delete the user's tasks

    def save(self, **kwargs):
        self.validate_unique()
        return super().save(**kwargs)
