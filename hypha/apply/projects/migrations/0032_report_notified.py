# Generated by Django 2.1.11 on 2019-11-05 15:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0031_add_public_private_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="notified",
            field=models.DateTimeField(null=True),
        ),
    ]
