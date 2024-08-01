from django.db.models.signals import post_delete
from django.dispatch import receiver

from hypha.apply.todo.views import remove_tasks_of_related_obj

from .models.project import DRAFT, INTERNAL_APPROVAL, PAFReviewersRole, Project


@receiver(post_delete, sender=PAFReviewersRole)
def handle_internal_approval_projects(sender, instance, **kwargs):
    # if last Project reviewer role
    if PAFReviewersRole.objects.count() == 0:
        for project in Project.objects.filter(status=INTERNAL_APPROVAL):
            # remove all paf approvals(approved and unapproved both)
            project.paf_approvals.all().delete()
            # update project status back to Draft
            project.status = DRAFT
            project.save(update_fields=["status"])
            # remove all tasks for internal_approval project
            remove_tasks_of_related_obj(project)
