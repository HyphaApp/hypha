# Generated by Django 4.2.16 on 2024-09-10 07:34

from django.db import migrations


class Migration(migrations.Migration):
    def copy_homepage_title_and_strapline(apps, schema_editor):
        from hypha.core.models import SystemSettings
        from hypha.home.models import ApplyHomePage

        if home_page := ApplyHomePage.objects.first():
            system_settings = SystemSettings.load()
            system_settings.home_title = home_page.title
            system_settings.home_strapline = home_page.strapline
            system_settings.save()

    dependencies = [
        ("core", "0006_systemsettings_home_strapline_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_homepage_title_and_strapline),
    ]