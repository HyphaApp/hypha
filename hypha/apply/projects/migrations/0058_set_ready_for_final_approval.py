# Generated by Django 3.2.16 on 2023-01-10 07:07

from django.db import migrations


def is_paf_approved_by_all_reviewers(project, paf_reviewers_count):
    if paf_reviewers_count == 0:
        return True
    elif paf_reviewers_count == len(project.paf_reviews_meta_data):
        for paf_review_data in project.paf_reviews_meta_data.values():
            if paf_review_data['status'] == 'request_change':
                return False
        return True
    return False


def set_value_to_ready_for_final_approval(apps, schema_editor):
    Project = apps.get_model('application_projects', 'Project')
    PAFReviewersRole = apps.get_model('application_projects', 'PAFReviewersRole')

    for project in Project.objects.filter(status='waiting_for_approval', ready_for_final_approval=False):
        if is_paf_approved_by_all_reviewers(project, PAFReviewersRole.objects.all().count()):
            project.ready_for_final_approval = True
            project.save(update_fields={'ready_for_final_approval'})


class Migration(migrations.Migration):

    dependencies = [
        ('application_projects', '0057_project_ready_for_final_approval'),
    ]

    operations = [
        migrations.RunPython(set_value_to_ready_for_final_approval)
    ]
