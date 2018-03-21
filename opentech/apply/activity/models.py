from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from opentech.apply.funds.models import ApplicationSubmission

COMMENT = 'comment'
ACTION = 'action'

ACTIVITY_TYPES = {
    COMMENT: 'Comment',
    ACTION: 'Action',
}

PUBLIC = 'public'
INTERNAL = 'internal'

VISIBILITY = {
    PUBLIC: 'Public',
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
            return [PUBLIC, INTERNAL]
        return [PUBLIC]

    @classmethod
    def visibility_choices_for(cls, user):
        return [(choice, VISIBILITY[choice]) for choice in cls.visibility_for(user)]


@receiver(post_save, sender=ApplicationSubmission)
def log_submission_activity(sender, **kwargs):
    if kwargs.get('created', False):
        submission = kwargs.get('instance')

        Activity.actions.create(
            user=submission.user,
            submission=submission,
            message=f'Submitted {submission.title} for {submission.page.title}'
        )
