# Generated by Django 2.0.2 on 2018-03-13 12:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0003_activity_visibility"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activity",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
