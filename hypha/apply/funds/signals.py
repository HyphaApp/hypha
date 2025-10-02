from django.db.models.signals import pre_delete
from django.dispatch import receiver

from hypha.apply.funds.models.application_revisions import ApplicationRevision
from hypha.apply.funds.models.mixins import AccessFormData
from hypha.apply.funds.models.submissions import ApplicationSubmission


@receiver(signal=pre_delete, sender=ApplicationSubmission)
@receiver(signal=pre_delete, sender=ApplicationRevision)
def delete_attachments(sender, instance=None, **kwargs):
    """
    Before the deletion of any sub class of AccessFormData, ensure the files associated with it are deleted too.

    This can include things like ApplicationSubmission & ApplicationRevision objects
    """
    # This will be called anytime a deletion is ran, so ensure the object being deleted
    # can have attachments
    if (
        sender
        and issubclass(sender, AccessFormData)
        and isinstance(instance, AccessFormData)
    ):
        files = instance.extract_files()
        for value in files.values():
            if not isinstance(value, list):  # Single file field
                value.delete()
            else:  # Multiple file fields
                [sub_file.delete() for sub_file in value]
