# Generated by Django 2.0.9 on 2019-02-22 15:06

from django.db import migrations, models
import wagtail.search.index


class Migration(migrations.Migration):
    dependencies = [
        ("categories", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MetaCategory",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                (
                    "name",
                    models.CharField(
                        help_text="Keep the name short, ideally one word.",
                        max_length=50,
                        unique=True,
                    ),
                ),
                (
                    "node_order_index",
                    models.IntegerField(blank=True, default=0, editable=False),
                ),
            ],
            options={
                "verbose_name": "Meta Category",
                "verbose_name_plural": "Meta Categories",
            },
            bases=(wagtail.search.index.Indexed, models.Model),
        ),
    ]
