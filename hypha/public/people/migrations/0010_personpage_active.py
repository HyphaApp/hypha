# Generated by Django 2.0.2 on 2018-08-29 17:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0009_dont_insist_on_first_name_or_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="personpage",
            name="active",
            field=models.BooleanField(default=True),
        ),
    ]
