from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.fields import StreamField

from opentech.apply.funds.models.mixins import AccessFormData
from opentech.apply.review.options import YES, NO, MAYBE, RECOMMENDATION_CHOICES
from opentech.apply.stream_forms.models import BaseStreamForm
from opentech.apply.users.models import User

from .blocks import ReviewCustomFormFieldsBlock


class ReviewForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(ReviewCustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class ReviewQuerySet(models.QuerySet):
    def submitted(self):
        return self.filter(is_draft=False)

    def by_staff(self):
        return self.submitted().filter(author__in=User.objects.staff())

    def by_reviewers(self):
        return self.submitted().filter(author__in=User.objects.reviewers())

    def staff_score(self):
        return self.by_staff().score()

    def staff_recommendation(self):
        return self.by_staff().recommendation()

    def reviewers_score(self):
        return self.by_reviewers().score()

    def reviewers_recommendation(self):
        return self.by_reviewers().recommendation()

    def score(self):
        return self.aggregate(models.Avg('score'))['score__avg']

    def recommendation(self):
        recommendations = self.values_list('recommendation', flat=True)
        try:
            recommendation = sum(recommendations) / len(recommendations)
        except ZeroDivisionError:
            return -1

        if recommendation == YES or recommendation == NO:
            # If everyone in agreement return Yes/No
            return recommendation
        else:
            return MAYBE


class Review(BaseStreamForm, AccessFormData, models.Model):
    submission = models.ForeignKey('funds.ApplicationSubmission', on_delete=models.CASCADE, related_name='reviews')
    revision = models.ForeignKey('funds.ApplicationRevision', on_delete=models.SET_NULL, related_name='reviews', null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )

    form_data = JSONField(default=dict, encoder=DjangoJSONEncoder)
    form_fields = StreamField(ReviewCustomFormFieldsBlock())

    recommendation = models.IntegerField(verbose_name="Recommendation", choices=RECOMMENDATION_CHOICES, default=0)
    score = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    is_draft = models.BooleanField(default=False, verbose_name="Draft")

    objects = ReviewQuerySet.as_manager()

    class Meta:
        unique_together = ('author', 'submission')

    @property
    def outcome(self):
        return self.get_recommendation_display()

    def get_absolute_url(self):
        return reverse('apply:reviews:review', args=(self.id,))

    def __str__(self):
        return f'Review for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.form_data)}>'

    @property
    def for_latest(self):
        return self.revision == self.submission.live_revision

    def get_compare_url(self):
        return reverse("funds:submissions:revisions:compare", kwargs={
            'submission_pk': self.submission.id,
            'to': self.submission.live_revision.id,
            'from': self.revision.id,
        })


@receiver(post_save, sender=Review)
def update_submission_reviewers_list(sender, **kwargs):
    review = kwargs.get('instance')

    # Make sure the reviewer is in the reviewers list on the submission
    if not review.submission.reviewers.filter(id=review.author.id).exists():
        review.submission.reviewers.add(review.author)
