from django.db.models.signals import pre_delete
from django.dispatch import receiver

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.services import convert_to_skeleton_submission
from hypha.apply.users.models import User


@receiver(signal=pre_delete, sender=User)
def skeletonize_user_submissions(sender, instance=None, **kwargs):
    for submission in ApplicationSubmission.objects.filter(user=instance):
        convert_to_skeleton_submission(submission, save_user=False)
