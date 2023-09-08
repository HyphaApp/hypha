# Generated by Django 2.0.13 on 2019-09-12 12:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="systemmessagessettings",
            options={"verbose_name": "system settings"},
        ),
        migrations.AddField(
            model_name="systemmessagessettings",
            name="footer_content",
            field=models.TextField(
                default="<p>Configure this text in Wagtail admin -> Settings -> System settings.</p>",
                help_text="This will be added to the footer, html tags is allowed.",
                verbose_name="Footer content",
            ),
        ),
    ]
