# Generated by Django 2.2.24 on 2021-10-28 14:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('funds', '0088_auto_20210423_1257'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='applicationbase',
            name='approval_form',
        ),
        migrations.RemoveField(
            model_name='labbase',
            name='approval_form',
        ),
    ]
