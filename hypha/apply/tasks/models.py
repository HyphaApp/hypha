from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import ValidationError
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
        if not self.user and not self.user_group:
            raise ValidationError("Task should be assigned to a user or a user group")

    def validate_unique(self, exclude=None):
        if self.user:
            if Task.objects.filter(
                code=self.code,
                user=self.user,
                related_content_type=ContentType.objects.get_for_model(
                    self.related_object
                ).id,
                related_object_id=self.related_object.id,
            ).exists():
                raise ValidationError("Task is already assigned to the user")
            # :todo: need to lookup for exact user groups(many to many)
            if Task.objects.filter(
                code=self.code,
                user_group=self.user.groups.all(),
                related_content_type=ContentType.objects.get_for_model(
                    self.related_object
                ).id,
                related_object_id=self.related_object.id,
            ).exists():
                raise ValidationError("Task is already assigned to user's group")
        if self.user_group:
            if Task.objects.filter(
                code=self.code,
                user_group=self.user_group,
                related_content_type=ContentType.objects.get_for_model(
                    self.related_object
                ).id,
                related_object_id=self.related_object.id,
            ).eixsts():
                raise ValidationError("Task is already assigned to the user group")
            if Task.objects.filter(
                code=self.code,
                user__groups=self.user_group,
                related_content_type=ContentType.objects.get_for_model(
                    self.related_object
                ).id,
                related_object_id=self.related_object.id,
            ).eixsts():
                # removed same task for individual and add it to a user group
                Task.objects.filter(
                    code=self.code,
                    user__groups=self.user_group,
                    related_content_type=ContentType.objects.get_for_model(
                        self.related_object
                    ).id,
                    related_object_id=self.related_object.id,
                ).delete()
                pass

    def save(self, **kwargs):
        self.validate_unique()
        return super().save(**kwargs)
