# Generated by Django 4.2.21 on 2025-05-12 19:58

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0100_alter_project_proposed_end_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="message_for_pm",
            field=models.TextField(
                blank=True,
                help_text="This will be displayed as a comment in the comments tab",
                verbose_name="Comment",
            ),
        ),
    ]
