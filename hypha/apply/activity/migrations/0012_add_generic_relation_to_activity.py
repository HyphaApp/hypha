# Generated by Django 2.0.2 on 2018-09-06 09:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("activity", "0011_add_new_event_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="activity",
            name="content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="activity",
            name="object_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
