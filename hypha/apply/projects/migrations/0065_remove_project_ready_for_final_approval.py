# Generated by Django 3.2.18 on 2023-03-06 04:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('application_projects', '0064_alter_pafapprovals_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='ready_for_final_approval',
        ),
    ]
