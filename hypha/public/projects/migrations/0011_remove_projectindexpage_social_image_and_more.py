# Generated by Django 4.2.9 on 2024-01-07 18:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0010_alter_projectpage_body"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="projectindexpage",
            name="social_image",
        ),
        migrations.RemoveField(
            model_name="projectindexpage",
            name="social_text",
        ),
        migrations.RemoveField(
            model_name="projectpage",
            name="social_image",
        ),
        migrations.RemoveField(
            model_name="projectpage",
            name="social_text",
        ),
    ]
