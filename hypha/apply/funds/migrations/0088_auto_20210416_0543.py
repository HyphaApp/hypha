# Generated by Django 2.2.19 on 2021-04-16 05:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('funds', '0087_applicationsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='assign',
            field=models.CharField(blank=True, choices=[('Applicant', 'APPLICANT'), ('Partners', 'PARTNERS'), ('Lead', 'LEAD'), ('Reviewers', 'REVIEWERS'), ('Team', 'TEAM')], default='none', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='title',
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
    ]
