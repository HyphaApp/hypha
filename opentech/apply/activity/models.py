from django.conf import settings
from django.db import models

COMMENT = 'comment'
ACTION = 'action'

ACTIVITY_TYPES = {
    COMMENT: 'Comment',
    ACTION: 'Action',
}


class ActivityBaseManager(models.Manager):
    def create(self, **kwargs):
        kwargs.update(type=self.type)
        return super().create(**kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(type=self.type)


class CommentManger(ActivityBaseManager):
    type = COMMENT


class ActionManager(ActivityBaseManager):
    type = ACTION


class Activity(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(choices=ACTIVITY_TYPES.items(), max_length=30)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    submission = models.ForeignKey('funds.ApplicationSubmission', related_name='activities')
    message = models.TextField()

    objects = models.Manager()
    comments = CommentManger()
    actions = ActionManager()

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return '{}: for "{}"'.format(self.get_type_display(), self.submission)
