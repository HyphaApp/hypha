# Generated by Django 4.2.9 on 2024-01-07 18:52

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0014_alter_newspagenewstype_news_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="newsindex",
            name="social_image",
        ),
        migrations.RemoveField(
            model_name="newsindex",
            name="social_text",
        ),
        migrations.RemoveField(
            model_name="newspage",
            name="social_image",
        ),
        migrations.RemoveField(
            model_name="newspage",
            name="social_text",
        ),
    ]
