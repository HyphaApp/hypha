# Generated by Django 4.2.11 on 2024-06-06 20:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_move_system_settings_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="systemsettings",
            name="footer_content",
            field=models.TextField(
                blank=True,
                default='"<p>Configure this text in Wagtail admin -> Settings -> System settings.</p>\n<br>\n<a href="#" onclick="openConsentPrompt()">Cookie Settings</a>"',
                help_text="This will be added to the footer, html tags is allowed.",
                verbose_name="Footer content",
            ),
        ),
    ]
