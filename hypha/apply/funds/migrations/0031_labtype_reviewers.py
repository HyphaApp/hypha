# Generated by Django 2.0.2 on 2018-03-13 15:15

from django.conf import settings
from django.db import migrations
import modelcluster.fields


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("funds", "0030_add_reviewers"),
    ]

    operations = [
        migrations.AddField(
            model_name="labtype",
            name="reviewers",
            field=modelcluster.fields.ParentalManyToManyField(
                limit_choices_to={"groups__name": "Reviewer"},
                related_name="labs_reviewer",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
