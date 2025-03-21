# Generated by Django 4.2.17 on 2025-01-07 17:57

from django.db import migrations
from hypha.apply.activity.models import COMMENT


def migrate_project_comments_to_application(apps, schema_editor):
    Activity = apps.get_model("activity", "Activity")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Project = apps.get_model("application_projects", "Project")
    ApplicationSubmission = apps.get_model("funds", "ApplicationSubmission")
    project_type = ContentType.objects.get_for_model(Project)
    application_type = ContentType.objects.get_for_model(ApplicationSubmission)
    for comment in Activity.objects.filter(
        type=COMMENT, source_content_type=project_type
    ):
        application = Project.objects.get(id=comment.source_object_id).submission
        comment.source_content_type = application_type
        comment.source_object_id = application.id
        comment.save()


class Migration(migrations.Migration):
    dependencies = [
        ("application_projects", "0097_help_text_rich_text"),
    ]

    operations = [migrations.RunPython(migrate_project_comments_to_application)]
