# Generated by Django 4.2.11 on 2024-05-31 14:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0085_projectsettings_staff_upload_contract"),
    ]

    operations = [
        migrations.AddField(
            model_name="projectsettings",
            name="upload_countersigned_contract",
            field=models.BooleanField(
                default=False,
                help_text="Check to require that uploaded contracts already be signed (countersigned) by all parties. In effect, this means two contract upload steps are reduced to a single step.",
            ),
        ),
    ]
