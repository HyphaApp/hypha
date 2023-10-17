# Generated by Django 2.0.2 on 2018-03-14 11:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("review", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConceptReview",
            fields=[
                (
                    "review_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="review.Review",
                    ),
                ),
            ],
            bases=("review.review",),
        ),
        migrations.CreateModel(
            name="ProposalReview",
            fields=[
                (
                    "review_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="review.Review",
                    ),
                ),
            ],
            bases=("review.review",),
        ),
        migrations.AddField(
            model_name="review",
            name="recommendation",
            field=models.IntegerField(
                choices=[(0, "No"), (1, "Maybe"), (2, "Yes")],
                default=0,
                verbose_name="Recommendation",
            ),
        ),
        migrations.AddField(
            model_name="review",
            name="score",
            field=models.DecimalField(decimal_places=1, default=0, max_digits=10),
        ),
    ]
