from django.conf import settings
from django.db import models
from django.db.models import Case, When, Value
from django.db.models.functions import Concat

from .messaging import MESSAGES


COMMENT = 'comment'
ACTION = 'action'

ACTIVITY_TYPES = {
    COMMENT: 'Comment',
    ACTION: 'Action',
}

PUBLIC = 'public'
REVIEWER = 'reviewers'
INTERNAL = 'internal'


VISIBILILTY_HELP_TEXT = {
    PUBLIC: 'Visible to all users of application system.',
    REVIEWER: 'Visible to reviewers and staff.',
    INTERNAL: 'Visible only to staff.',
}


VISIBILITY = {
    PUBLIC: 'Public',
    REVIEWER: 'Reviewers',
    INTERNAL: 'Internal',
}


class BaseActivityQuerySet(models.QuerySet):
    def visible_to(self, user):
        return self.filter(visibility__in=self.model.visibility_for(user))


class ActivityQuerySet(BaseActivityQuerySet):
    def comments(self):
        return self.filter(type=COMMENT)

    def actions(self):
        return self.filter(type=ACTION)


class ActivityBaseManager(models.Manager):
    def create(self, **kwargs):
        kwargs.update(type=self.type)
        return super().create(**kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(type=self.type)


class CommentQueryset(BaseActivityQuerySet):
    pass


class CommentManger(ActivityBaseManager):
    type = COMMENT


class ActionManager(ActivityBaseManager):
    type = ACTION


class Activity(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    type = models.CharField(choices=ACTIVITY_TYPES.items(), max_length=30)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    submission = models.ForeignKey('funds.ApplicationSubmission', related_name='activities', on_delete=models.CASCADE)
    message = models.TextField()
    visibility = models.CharField(choices=VISIBILITY.items(), default=PUBLIC, max_length=10)

    objects = models.Manager.from_queryset(ActivityQuerySet)()
    comments = CommentManger.from_queryset(CommentQueryset)()
    actions = ActionManager()

    class Meta:
        ordering = ['-timestamp']
        base_manager_name = 'objects'

    @property
    def private(self):
        return self.visibility != PUBLIC

    def __str__(self):
        return '{}: for "{}"'.format(self.get_type_display(), self.submission)

    @classmethod
    def visibility_for(cls, user):
        if user.is_apply_staff:
            return [PUBLIC, REVIEWER, INTERNAL]
        if user.is_reviewer:
            return [PUBLIC, REVIEWER]
        return [PUBLIC]

    @classmethod
    def visibility_choices_for(cls, user):
        return [(choice, VISIBILITY[choice]) for choice in cls.visibility_for(user)]


class Event(models.Model):
    """Model to track when messages are triggered"""

    when = models.DateTimeField(auto_now_add=True)
    type = models.CharField(choices=MESSAGES.choices(), max_length=50)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    submission = models.ForeignKey('funds.ApplicationSubmission', related_name='+', on_delete=models.CASCADE)

    def __str__(self):
        return ' '.join([self.get_type_display(), 'by:', str(self.by), 'on:', self.submission.title])


class Message(models.Model):
    """Model to track content of messages sent from an event"""

    type = models.CharField(max_length=15)
    content = models.TextField()
    recipient = models.CharField(max_length=250)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.TextField()

    def update_status(self, status):
        if status:
            self.status = Case(
                When(status='', then=Value(status)),
                default=Concat('status', Value('<br />' + status))
            )
            self.save()
