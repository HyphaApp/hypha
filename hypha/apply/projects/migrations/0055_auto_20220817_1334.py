# Generated by Django 3.2.15 on 2022-08-17 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application_projects', '0054_alter_project_form_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='packetfile',
            name='name_mentioned_in_contract',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='packetfile',
            name='sign_autoritive_person_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
