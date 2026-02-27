from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from hypha.apply.review.options import AGREE, DISAGREE

from .utils import (
    COMMUNITY_REVIEWER_GROUP_NAME,
    LIMIT_TO_REVIEWER_GROUPS,
    REVIEW_GROUPS,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
)


class AssignedReviewersQuerySet(models.QuerySet):
    def review_order(self):
        review_order = [
            STAFF_GROUP_NAME,
            COMMUNITY_REVIEWER_GROUP_NAME,
            REVIEWER_GROUP_NAME,
        ]

        ordering = [
            models.When(type__name=review_type, then=models.Value(i))
            for i, review_type in enumerate(review_order)
        ]
        return (
            self.exclude(
                # Remove people from the list who are opinionated but
                # didn't submit a review, they appear elsewhere
                Q(opinions__isnull=False)
                & Q(Q(review__isnull=True) | Q(review__is_draft=True))
            )
            .annotate(
                type_order=models.Case(
                    *ordering,
                    output_field=models.IntegerField(),
                ),
                has_review=models.Case(
                    models.When(review__isnull=True, then=models.Value(1)),
                    models.When(review__is_draft=True, then=models.Value(1)),
                    default=models.Value(0),
                    output_field=models.IntegerField(),
                ),
            )
            .order_by(
                "type_order",
                "has_review",
                F("role__order").asc(nulls_last=True),
            )
            .select_related(
                "reviewer",
                "role",
            )
        )

    def with_roles(self):
        return self.filter(role__isnull=False)

    def without_roles(self):
        return self.filter(role__isnull=True)

    def reviewed(self):
        return self.filter(
            Q(opinions__opinion=AGREE)
            | Q(Q(review__isnull=False) & Q(review__is_draft=False))
        ).distinct()

    def draft_reviewed(self):
        return self.filter(
            Q(Q(review__isnull=False) & Q(review__is_draft=True))
        ).distinct()

    def not_reviewed(self):
        return self.filter(
            Q(review__isnull=True) | Q(review__is_draft=True),
            Q(opinions__isnull=True) | Q(opinions__opinion=DISAGREE),
        ).distinct()

    def never_tried_to_review(self):
        # Different from not reviewed as draft reviews allowed
        return self.filter(
            review__isnull=True,
            opinions__isnull=True,
        )

    def staff(self):
        return self.filter(type__name=STAFF_GROUP_NAME)

    def get_or_create_for_user(self, submission, reviewer):
        groups = set(reviewer.groups.values_list("name", flat=True)) & set(
            REVIEW_GROUPS
        )
        if len(groups) > 1:
            if COMMUNITY_REVIEWER_GROUP_NAME in groups:
                groups = {COMMUNITY_REVIEWER_GROUP_NAME}
            elif reviewer.is_apply_staff:
                groups = {STAFF_GROUP_NAME}
            else:
                groups = {REVIEWER_GROUP_NAME}
        elif not groups:
            if reviewer.is_staff or reviewer.is_superuser:
                groups = {STAFF_GROUP_NAME}
            else:
                groups = {REVIEWER_GROUP_NAME}

        group = Group.objects.get(name=groups.pop())

        return self.get_or_create(
            submission=submission,
            reviewer=reviewer,
            defaults={"type": group},
        )

    def get_or_create_staff(self, submission, reviewer):
        return self.get_or_create(
            submission=submission,
            reviewer=reviewer,
            type=Group.objects.get(name=STAFF_GROUP_NAME),
        )

    def bulk_create_reviewers(self, reviewers, submission):
        group = Group.objects.get(name=REVIEWER_GROUP_NAME)
        self.bulk_create(
            [
                self.model(
                    submission=submission,
                    role=None,
                    reviewer=reviewer,
                    type=group,
                )
                for reviewer in reviewers
            ],
            ignore_conflicts=True,
        )

    def update_role(self, role, reviewer, *submissions):
        # Remove role who didn't review
        self.filter(
            submission__in=submissions, role=role
        ).never_tried_to_review().delete()
        # Anyone else we remove their role
        self.filter(submission__in=submissions, role=role).update(role=None)
        # Create/update the new role reviewers
        group = Group.objects.get(name=STAFF_GROUP_NAME)
        for submission in submissions:
            self.update_or_create(
                submission=submission,
                reviewer=reviewer,
                defaults={"role": role, "type": group},
            )


class AssignedReviewers(models.Model):
    wagtail_reference_index_ignore = True

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=LIMIT_TO_REVIEWER_GROUPS,
    )
    type = models.ForeignKey(
        "auth.Group",
        on_delete=models.PROTECT,
    )
    submission = models.ForeignKey(
        "funds.ApplicationSubmission", related_name="assigned", on_delete=models.CASCADE
    )
    role = models.ForeignKey(
        "funds.ReviewerRole",
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
    )

    objects = AssignedReviewersQuerySet.as_manager()

    class Meta:
        unique_together = (("submission", "role"), ("submission", "reviewer"))
        verbose_name = _("assigned reviewer")
        verbose_name_plural = _("assigned reviewers")

    def __hash__(self):
        return hash(self.pk)

    def __str__(self):
        return f"{self.reviewer}"

    def __eq__(self, other):
        if not isinstance(other, models.Model):
            return False
        if self._meta.concrete_model != other._meta.concrete_model:
            return False
        my_pk = self.pk
        if my_pk is None:
            return self is other
        return all(
            [
                self.reviewer_id == other.reviewer_id,
                self.role_id == other.role_id,
            ]
        )
