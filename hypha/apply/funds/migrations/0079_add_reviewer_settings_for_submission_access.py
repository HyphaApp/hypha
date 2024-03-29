# Generated by Django 2.2.15 on 2020-08-27 21:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("wagtailcore", "0045_assign_unlock_grouppagepermission"),
        ("funds", "0078_add_heading_block_to_form_fields_block"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewerSettings",
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
                (
                    "submission",
                    models.CharField(
                        choices=[
                            ("all", "All Submissions"),
                            ("reviewed", "Only reviewed Submissions"),
                        ],
                        default="all",
                        help_text="Submissions for which reviewers should have access to",
                        max_length=10,
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("all", "All States"),
                            ("ext_state_or_higher", "Only External review and higher"),
                        ],
                        default="all",
                        help_text="Submissions states for which reviewers should have access to",
                        max_length=20,
                    ),
                ),
                (
                    "outcome",
                    models.CharField(
                        choices=[
                            ("all", "All Outcomes"),
                            ("accepted", "Only Accepted"),
                        ],
                        default="all",
                        help_text="Submissions outcomes for which reviewers should have access to",
                        max_length=10,
                    ),
                ),
                (
                    "assigned",
                    models.BooleanField(
                        default=False,
                        help_text="Submissions for which reviewer is assigned to",
                    ),
                ),
                (
                    "use_settings",
                    models.BooleanField(
                        default=False,
                        help_text="Use the above configured variables to filter out submissions",
                    ),
                ),
                (
                    "site",
                    models.OneToOneField(
                        editable=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="wagtailcore.Site",
                    ),
                ),
            ],
            options={
                "verbose_name": "Reviewer Settings",
            },
        ),
    ]
