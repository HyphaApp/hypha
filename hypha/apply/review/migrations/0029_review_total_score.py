import json

from django.db import migrations, models

from hypha.apply.review.options import NA

# Block types are matched by name rather than class: the historical streamfield
# definition deconstructs the score blocks to plain StructBlocks, so the
# ScoreFieldBlock helpers on the model are not available here. The names are
# what is stored in "form_fields", so they cannot change without a migration of
# their own.
SCORE = "score"
SCORE_WITHOUT_TEXT = "score_without_text"


def get_scores(review):
    """Return the individual scores in a review, NA and blank answers as 0."""
    scores = []
    for field in review.form_fields.raw_data:
        if field["type"] not in (SCORE, SCORE_WITHOUT_TEXT):
            continue

        answer = review.form_data.get(field.get("id"))
        if field["type"] == SCORE:
            if isinstance(answer, str):
                # Scored answers used to be stored as JSON.
                answer = json.loads(answer)
            score = answer[1] if answer else NA
            if int(score) == NA:
                score = 0
        else:
            score = answer or 0

        scores.append(int(score))
    return scores


def calculate_total_scores(apps, schema_editor):
    Review = apps.get_model("review", "Review")

    for review in Review.objects.iterator():
        scores = get_scores(review)
        # A queryset update leaves "updated_at" untouched.
        Review.objects.filter(pk=review.pk).update(
            total_score=sum(scores) if scores else NA
        )


def revert_total_scores(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("review", "0028_alter_review_options_alter_reviewform_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="total_score",
            field=models.DecimalField(decimal_places=1, default=0, max_digits=10),
        ),
        migrations.RunPython(calculate_total_scores, revert_total_scores),
    ]
