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
    MEDIUM = {
        REVIEW: EMAIL
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
        default=REVIEW,
        max_length=50,
    )
    sent = models.BooleanField(default=False)

    def __str__(self):
        return '{} at {}'.format(
            self.ACTIONS[self.action],
            self.time.strftime('%Y-%m-%d  %I:%M %p')
        )

    class Meta:
        ordering = ['-time']

    @property
    def is_expired(self):
        return timezone.now() > self.time

    @property
    def action_message(self):
        return self.ACTION_MESSAGE[f'{self.action}-{self.medium}']

    @property
    def medium(self):
        return self.MEDIUM[self.action]
