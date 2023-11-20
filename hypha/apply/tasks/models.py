from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

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

    def save(self, **kwargs):
        return super().save(**kwargs)
