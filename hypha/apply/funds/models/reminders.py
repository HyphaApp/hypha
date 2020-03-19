from django.conf import settings
from django.db import models
from django.utils import timezone

from hypha.apply.activity.messaging import MESSAGES


class Reminder(models.Model):
    REVIEW = 'reviewers_review'
    ACTIONS = {
        REVIEW: 'Remind reviewers to Review',
    }
    EMAIL = 'email'
    MEDIUM_TYPES = {
        EMAIL: 'Email',
    }
    ACTION_MESSAGE = {
        f'{REVIEW}-{EMAIL}': MESSAGES.REVIEW_REMINDER,
    }
    submission = models.ForeignKey(
        'funds.ApplicationSubmission',
        on_delete=models.CASCADE,
        related_name='reminders'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    time = models.DateTimeField()
    action = models.CharField(
        choices=ACTIONS.items(),
        max_length=50,
    )
    medium = models.CharField(
        choices=MEDIUM_TYPES.items(),
        default=EMAIL,
        max_length=15,
    )
    sent = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.ACTIONS[self.action]} at {self.time_with_format}'

    class Meta:
        ordering = ['-time']

    @property
    def is_expired(self):
        return timezone.now() > self.time

    @property
    def time_with_format(self):
        return self.time.strftime('%Y-%m-%d  %I:%M %p')

    @property
    def action_message(self):
        return self.ACTION_MESSAGE[f'{self.action}-{self.medium}']
