# Generated by Django 2.0.2 on 2018-08-02 09:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailcore", "0040_page_draft_title"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("review", "0006_remove_review_review"),
        ("funds", "0036_fundreviewform_labreviewform"),
    ]

    operations = [
        # Rename all the existing models as required
        migrations.RenameModel(
            old_name="FundType",
            new_name="ApplicationBase",
        ),
        migrations.RenameModel(
            old_name="Round",
            new_name="RoundBase",
        ),
        migrations.RenameModel(
            old_name="LabType",
            new_name="LabBase",
        ),
        migrations.RenameModel(
            old_name="FundForm",
            new_name="ApplicationBaseForm",
        ),
        migrations.RenameModel(
            old_name="FundReviewForm",
            new_name="ApplicationBaseReviewForm",
        ),
        migrations.RenameModel(
            old_name="LabForm",
            new_name="LabBaseForm",
        ),
        migrations.RenameModel(
            old_name="LabReviewForm",
            new_name="LabBaseReviewForm",
        ),
        migrations.RenameModel(
            old_name="RoundForm",
            new_name="RoundBaseForm",
        ),
        # Add all the new models
        migrations.CreateModel(
            name="FundType",
            fields=[
                (
                    "applicationbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="funds.ApplicationBase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fund",
            },
            bases=("funds.applicationbase",),
        ),
        migrations.CreateModel(
            name="LabType",
            fields=[
                (
                    "labbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="funds.LabBase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lab",
            },
            bases=("funds.labbase",),
        ),
        migrations.CreateModel(
            name="Round",
            fields=[
                (
                    "roundbase_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="funds.RoundBase",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("funds.roundbase",),
        ),
        # Remove options - django
        migrations.AlterModelOptions(
            name="applicationbase",
            options={},
        ),
        migrations.AlterModelOptions(
            name="labbase",
            options={},
        ),
        # Rename fields as required - non essential
        migrations.RenameField(
            model_name="applicationbaseform",
            old_name="fund",
            new_name="application",
        ),
        migrations.RenameField(
            model_name="applicationbasereviewform",
            old_name="fund",
            new_name="application",
        ),
        # Alter related name based on the classname - non essential just being tidy
        migrations.AlterField(
            model_name="applicationbase",
            name="reviewers",
            field=modelcluster.fields.ParentalManyToManyField(
                blank=True,
                limit_choices_to={"groups__name": "Reviewer"},
                related_name="applicationbase_reviewers",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="roundbase",
            name="lead",
            field=models.ForeignKey(
                limit_choices_to={"groups__name": "Staff"},
                on_delete=django.db.models.deletion.PROTECT,
                related_name="roundbase_lead",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="roundbase",
            name="reviewers",
            field=modelcluster.fields.ParentalManyToManyField(
                blank=True,
                limit_choices_to={"groups__name": "Reviewer"},
                related_name="roundbase_reviewer",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
