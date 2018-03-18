from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models


RECOMMENDATION_CHOICES = (
    (0, 'No'),
    (1, 'Yes'),
    (2, 'Maybe')
)


class Review(models.Model):
    submission = models.ForeignKey('funds.ApplicationSubmission', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    review = JSONField()
    recommendation = models.IntegerField(verbose_name="Recommendation", choices=RECOMMENDATION_CHOICES, default=0)
    score = models.DecimalField(max_digits=10, decimal_places=1, default=0)

    class Meta:
        unique_together = ('author', 'submission')

    def __str__(self):
        return f'Review for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.review)}>'
