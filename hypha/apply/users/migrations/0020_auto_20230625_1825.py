# Generated by Django 3.2.19 on 2023-06-25 18:25

from django.db import migrations, models
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0019_rename_usersettings_authsettings"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="authsettings",
            options={"verbose_name": "Auth Settings"},
        ),
        migrations.RemoveField(
            model_name="authsettings",
            name="site",
        ),
        migrations.AddField(
            model_name="authsettings",
            name="register_extra_text",
            field=wagtail.fields.RichTextField(
                blank=True, help_text="Extra text to be displayed on register form"
            ),
        ),
        migrations.AlterField(
            model_name="authsettings",
            name="consent_show",
            field=models.BooleanField(
                default=False, verbose_name="Show consent checkbox?"
            ),
        ),
        migrations.AlterField(
            model_name="authsettings",
            name="extra_text",
            field=wagtail.fields.RichTextField(
                blank=True,
                help_text="Displayed along side login form",
                verbose_name="Login extra text",
            ),
        ),
    ]
