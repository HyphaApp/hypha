from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.fields import StreamField

from opentech.apply.funds.models.mixins import AccessFormData
from opentech.apply.stream_forms.models import BaseStreamForm
from opentech.apply.users.models import User

from .blocks import (
    ReviewCustomFormFieldsBlock,
    RecommendationBlock,
    RecommendationCommentsBlock,
    ScoreFieldBlock,
    VisibilityBlock,
)
from .options import NA, YES, NO, MAYBE, RECOMMENDATION_CHOICES, OPINION_CHOICES, VISIBILITY, PRIVATE, REVIEWER


class ReviewFormFieldsMixin(models.Model):
    class Meta:
        abstract = True

    form_fields = StreamField(ReviewCustomFormFieldsBlock())

    @property
    def score_fields(self):
        return self._get_field_type(ScoreFieldBlock, many=True)

    @property
    def recommendation_field(self):
        return self._get_field_type(RecommendationBlock)

    @property
    def visibility_field(self):
        return self._get_field_type(VisibilityBlock)

    @property
    def comment_field(self):
        return self._get_field_type(RecommendationCommentsBlock)

    def _get_field_type(self, block_type, many=False):
        fields = list()
        for field in self.form_fields:
            try:
                if isinstance(field.block, block_type):
                    if many:
                        fields.append(field)
                    else:
                        return field
            except AttributeError:
                pass
        if many:
            return fields


class ReviewForm(ReviewFormFieldsMixin, models.Model):
    name = models.CharField(max_length=255)

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

    def by_partners(self):
        return self.submitted().filter(author__in=User.objects.partners())

    def staff_score(self):
        return self.by_staff().score()

    def staff_recommendation(self):
        return self.by_staff().recommendation()

    def reviewers_score(self):
        return self.by_reviewers().score()

    def reviewers_recommendation(self):
        return self.by_reviewers().recommendation()

    def score(self):
        return self.exclude(score=NA).aggregate(models.Avg('score'))['score__avg']

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

    def opinions(self):
        return ReviewOpinion.objects.filter(review__id__in=self.values_list('id'))


class Review(ReviewFormFieldsMixin, BaseStreamForm, AccessFormData, models.Model):
    submission = models.ForeignKey('funds.ApplicationSubmission', on_delete=models.CASCADE, related_name='reviews')
    revision = models.ForeignKey('funds.ApplicationRevision', on_delete=models.SET_NULL, related_name='reviews', null=True)
    author = models.OneToOneField(
        'funds.AssignedReviewers',
        related_name='review',
        on_delete=models.CASCADE,
    )

    form_data = JSONField(default=dict, encoder=DjangoJSONEncoder)

    recommendation = models.IntegerField(verbose_name=_("Recommendation"), choices=RECOMMENDATION_CHOICES, default=0)
    score = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    is_draft = models.BooleanField(default=False, verbose_name=_("Draft"))
    created_at = models.DateTimeField(verbose_name=_("Creation time"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Update time"), auto_now=True)
    visibility = models.CharField(verbose_name=_("Visibility"), choices=VISIBILITY.items(), default=PRIVATE, max_length=10)

    # Meta: used for migration purposes only
    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        unique_together = ('author', 'submission')

    @property
    def outcome(self):
        return self.get_recommendation_display()

    def get_comments_display(self, include_question=True):
        return self.render_answer(self.comment_field.id, include_question=include_question)

    @property
    def get_score_display(self):
        return '{:.1f}'.format(self.score) if self.score != NA else 'NA'

    def get_absolute_url(self):
        return reverse('apply:submissions:reviews:review', args=(self.submission.pk, self.id,))

    def __str__(self):
        return f'Review for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.form_data)}>'

    @property
    def for_latest(self):
        return self.revision == self.submission.live_revision

    def get_compare_url(self):
        return self.revision.get_compare_url_to_latest()

    @cached_property
    def reviewer_visibility(self):
        return self.visibility == REVIEWER


@receiver(post_save, sender=Review)
def update_submission_reviewers_list(sender, **kwargs):
    from opentech.apply.funds.models import AssignedReviewers
    review = kwargs.get('instance')

    # Make sure the reviewer is in the reviewers list on the submission
    AssignedReviewers.objects.get_or_create(
        submission=review.submission,
        reviewer=review.author,
    )


class ReviewOpinion(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='opinions')
    author = models.ForeignKey(
        'funds.AssignedReviewers',
        related_name='opinions',
        on_delete=models.CASCADE,
    )
    opinion = models.IntegerField(choices=OPINION_CHOICES)

    class Meta:
        unique_together = ('author', 'review')

    @property
    def opinion_display(self):
        return self.get_opinion_display()

    def get_author_role(self):
        assignment = self.review.submission.assigned.with_roles().filter(reviewer=self.author).first()
        return assignment.role if assignment else None
