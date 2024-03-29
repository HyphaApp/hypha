# Generated by Django 2.0.13 on 2019-07-10 17:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("activity", "0027_add_update_project_lead"),
    ]

    operations = [
        # Updates to the existing GenericForeignKey to related objects
        migrations.RenameField(
            model_name="activity",
            old_name="object_id",
            new_name="related_object_id",
        ),
        migrations.RenameField(
            model_name="activity",
            old_name="content_type",
            new_name="related_content_type",
        ),
        migrations.AlterField(
            model_name="activity",
            name="related_content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="activity_related",
                to="contenttypes.ContentType",
            ),
        ),
        # Add the new generic foreign key
        migrations.AddField(
            model_name="activity",
            name="source_content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="activity_source",
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="activity",
            name="source_object_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        # Make the submission field nullable
        migrations.AlterField(
            model_name="activity",
            name="submission",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="funds.ApplicationSubmission",
                related_name="activities",
                null=True,
            ),
        ),
    ]
