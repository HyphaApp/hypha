# Generated by Django 4.2.10 on 2024-03-11 15:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("funds", "0115_list_on_front_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="applicationrevision",
            name="is_preview",
            field=models.BooleanField(default=False),
        ),
    ]
