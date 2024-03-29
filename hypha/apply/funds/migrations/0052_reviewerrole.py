# Generated by Django 2.0.10 on 2019-02-07 15:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("images", "0003_customimage_drupal_id"),
        ("funds", "0051_applicationsubmission_partners"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewerRole",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                (
                    "order",
                    models.IntegerField(
                        blank=True,
                        help_text="The order this role should appear in the Update Reviewers form.",
                        null=True,
                    ),
                ),
                (
                    "icon",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="images.CustomImage",
                    ),
                ),
            ],
        ),
    ]
