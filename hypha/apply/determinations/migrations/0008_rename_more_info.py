# Generated by Django 2.1.11 on 2019-10-08 12:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("determinations", "0007_add_determinationformsettings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="determination",
            name="outcome",
            field=models.IntegerField(
                choices=[
                    (0, "Dismissed"),
                    (1, "More information requested"),
                    (2, "Approved"),
                ],
                default=1,
                verbose_name="Determination",
            ),
        ),
    ]
