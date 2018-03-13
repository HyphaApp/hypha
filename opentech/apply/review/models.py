from django.conf import settings
from django.db import models


class Review(models.Model):
    submission = models.ForeignKey('funds.ApplicationSubmission', on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    review = models.TextField()

    class Meta:
        unique_together = ('author', 'submission')
