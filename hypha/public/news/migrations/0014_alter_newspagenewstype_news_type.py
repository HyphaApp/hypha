# Generated by Django 4.1.8 on 2023-05-09 17:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0013_alter_newspage_body"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newspagenewstype",
            name="news_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="news.newstype",
            ),
        ),
    ]
