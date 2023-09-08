# Generated by Django 2.0.9 on 2019-02-24 03:16

from django.db import migrations
from django.core.exceptions import ObjectDoesNotExist

# Copied from hypha.apply.users.groups at time of migration to avoid
# importing and creating a future dependency. Changes to Group names should
# be handled in another migration

STAFF_GROUP_NAME = "Staff"
REVIEWER_GROUP_NAME = "Reviewer"
PARTNER_GROUP_NAME = "Partner"
COMMUNITY_REVIEWER_GROUP_NAME = "Community reviewer"

REVIEWER_GROUPS = {
    STAFF_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    COMMUNITY_REVIEWER_GROUP_NAME,
    PARTNER_GROUP_NAME,
}


def add_to_assigned_reviewers(apps, schema_editor):
    Review = apps.get_model("review", "Review")
    AssignedReviewer = apps.get_model("funds", "AssignedReviewers")
    Group = apps.get_model("auth", "Group")
    for review in Review.objects.select_related("author"):
        groups = (
            set(review.author.groups.values_list("name", flat=True)) & REVIEWER_GROUPS
        )
        if len(groups) > 1:
            if (
                PARTNER_GROUP_NAME in groups
                and review.author in review.submission.partners.all()
            ):
                groups = {PARTNER_GROUP_NAME}
            elif COMMUNITY_REVIEWER_GROUP_NAME in groups:
                groups = {COMMUNITY_REVIEWER_GROUP_NAME}
            elif review.author.is_staff or review.author.is_superuser:
                groups = {STAFF_GROUP_NAME}
            else:
                groups = {REVIEWER_GROUP_NAME}
        elif not groups:
            if review.author.is_staff or review.author.is_superuser:
                groups = {STAFF_GROUP_NAME}
            else:
                groups = {REVIEWER_GROUP_NAME}

        group = Group.objects.get(name=groups.pop())

        assignment, _ = AssignedReviewer.objects.update_or_create(
            submission=review.submission,
            reviewer=review.author,
            defaults={"type": group},
        )
        review.author_temp = assignment
        review.save()
        for opinion in review.opinions.select_related("author"):
            opinion_assignment, _ = AssignedReviewer.objects.update_or_create(
                submission=review.submission,
                reviewer=opinion.author,
                defaults={"type": Group.objects.get(name=STAFF_GROUP_NAME)},
            )
            opinion.author_temp = opinion_assignment
            opinion.save()


def add_to_review_and_opinion(apps, schema_editor):
    AssignedReviewer = apps.get_model("funds", "AssignedReviewers")
    for assigned in AssignedReviewer.objects.all():
        try:
            assigned.review.author = assigned.reviewer
            assigned.review.save()
        except ObjectDoesNotExist:
            pass
        if assigned.opinions.exists():
            for opinion in assigned.opinions.all():
                opinion.author = assigned.reviewer
                opinion.save()


class Migration(migrations.Migration):
    dependencies = [
        ("review", "0017_add_temp_author_field"),
        ("funds", "0063_make_reviewer_type_required"),
        ("users", "0010_add_community_reviewer_group"),
    ]

    operations = [
        migrations.RunPython(add_to_assigned_reviewers, add_to_review_and_opinion),
    ]
