from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models


from opentech.apply.users.models import User

NO = 0
MAYBE = 1
YES = 2

from opentech.apply.users.models import User

NO = 0
MAYBE = 1
YES = 2

RECOMMENDATION_CHOICES = (
    (NO, 'No'),
    (MAYBE, 'Maybe'),
    (YES, 'Yes'),
)


class ReviewQuerySet(models.QuerySet):
    def by_staff(self):
        return self.filter(author__in=User.objects.staff())

    def by_reviewers(self):
        return self.filter(author__in=User.objects.reviewers())

    def staff_score(self):
        return self.by_staff().score()

    def staff_reccomendation(self):
        return self.by_staff().reccomendation()

    def reviewers_score(self):
        return self.by_reviewers().score()

    def reviewers_reccomendation(self):
        return self.by_reviewers().reccomendation()

    def score(self):
        return self.aggregate(models.Avg('score'))['score__avg']

    def reccomendation(self):
        reccomendations = self.values_list('recommendation', flat=True)
        try:
            reccomendation = sum(reccomendations) / len(reccomendations)
        except ZeroDivisionError:
            return -1

        if reccomendation == YES or reccomendation == NO:
            # If everyone in agreement return Yes/No
            return reccomendation
        else:
            return MAYBE


class Review(models.Model):
    submission = models.ForeignKey('funds.ApplicationSubmission', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    review = JSONField()
    recommendation = models.IntegerField(verbose_name="Recommendation", choices=RECOMMENDATION_CHOICES, default=0)
    score = models.DecimalField(max_digits=10, decimal_places=1, default=0)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        unique_together = ('author', 'submission')

    def __str__(self):
        return f'Review for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.review)}>'
