# Generated by Django 4.2.11 on 2024-03-11 16:36

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0012_alter_systemmessagessettings_footer_content"),
        ("core", "0004_move_system_settings_data"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SystemMessagesSettings",
        ),
    ]