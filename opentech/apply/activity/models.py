from django.conf import settings
from django.db import models

COMMENT = 'comment'
ACTIVITY = 'activity'

ACTIVITY_TYPES = {
    COMMENT: 'Comment',
    ACTIVITY: 'Activity',
}


class CommentManger(models.Manager):
    def create(self, **kwargs):
        kwargs.update(type=COMMENT)
        return super().create(**kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(type=COMMENT)


class ActivityManager(models.Manager):
    def create(self, **kwargs):
        kwargs.update(type=ACTIVITY)
        return super().create(**kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(type=ACTIVITY)


class Activity(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(choices=ACTIVITY_TYPES.items(), max_length=30)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    submission = models.ForeignKey('funds.ApplicationSubmission', related_name='activities')
    message = models.TextField()

    objects = models.Manager()
    comments = CommentManger()
    activities = ActivityManager()

    class Meta:
        ordering = ['-timestamp']
