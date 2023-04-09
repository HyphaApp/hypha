from django.apps import apps
from django.db.models import (
    Case,
    Count,
    IntegerField,
    OuterRef,
    Prefetch,
    QuerySet,
    Subquery,
    Sum,
    When,
)

from hypha.apply.review.options import DISAGREE, MAYBE


def annotate_review_recommendation_and_count(submissions: QuerySet) -> QuerySet:
    Review = apps.get_model('review', 'Review')
    ReviewOpinion = apps.get_model('review', 'ReviewOpinion')
    AssignedReviewers = apps.get_model("funds", "AssignedReviewers")

    reviews = Review.objects.filter(submission=OuterRef('id'))
    opinions = ReviewOpinion.objects.filter(review__submission=OuterRef('id'))
    reviewers = AssignedReviewers.objects.filter(submission=OuterRef('id'))

    submissions = submissions.annotate(
        review_count=Subquery(
            reviewers.values('submission').annotate(count=Count('pk')).values('count'),
            output_field=IntegerField(),
        ),
        review_staff_count=Subquery(
            reviewers.staff()
            .values('submission')
            .annotate(count=Count('pk'))
            .values('count'),
            output_field=IntegerField(),
        ),
        review_submitted_count=Subquery(
            reviewers.reviewed()
            .values('submission')
            .annotate(count=Count('pk', distinct=True))
            .values('count'),
            output_field=IntegerField(),
        ),
        opinion_disagree=Subquery(
            opinions.filter(opinion=DISAGREE)
            .values('review__submission')
            .annotate(count=Count('*'))
            .values('count')[:1],
            output_field=IntegerField(),
        ),
        review_recommendation=Case(
            When(opinion_disagree__gt=0, then=MAYBE),
            default=Subquery(
                reviews.submitted()
                .values('submission')
                .annotate(
                    calc_recommendation=Sum('recommendation') / Count('recommendation'),
                )
                .values('calc_recommendation'),
                output_field=IntegerField(),
            ),
        ),
    ).prefetch_related(
        Prefetch(
            'assigned',
            queryset=AssignedReviewers.objects.reviewed()
            .review_order()
            .select_related(
                'reviewer',
            )
            .prefetch_related(
                Prefetch(
                    'review__opinions',
                    queryset=ReviewOpinion.objects.select_related('author'),
                ),
            ),
            to_attr='has_reviewed',
        ),
        Prefetch(
            'assigned',
            queryset=AssignedReviewers.objects.not_reviewed().staff(),
            to_attr='hasnt_reviewed',
        ),
    )
    return submissions
