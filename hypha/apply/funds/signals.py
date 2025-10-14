import sys

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from hypha.apply.funds.models.application_revisions import ApplicationRevision
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.utils import delete_directory


@receiver(signal=pre_delete, sender=ApplicationSubmission)
@receiver(signal=pre_delete, sender=ApplicationRevision)
def delete_attachments(sender, instance=None, **kwargs):
    """
    Before the deletion of any sub class of AccessFormData, ensure the files associated with it are deleted too.

    This can include things like ApplicationSubmission & ApplicationRevision objects
    """

    # TODO: This solution is not ideal but due to our unit tests writing to the filesystem
    #       this can cause files belonging to the dev's local server to be deleted. Until
    #       these can be better isolated, this signal will do nothing when pytest is running
    if "pytest" in sys.modules:
        return

    # This will be called anytime a deletion is ran, so ensure the object being deleted
    # can have attachments
    if issubclass(sender, ApplicationRevision):
        files = instance.extract_files()
        for value in files.values():
            if not isinstance(value, list):  # Single file field
                value.delete()
            else:  # Multiple file fields
                [sub_file.delete() for sub_file in value]
    elif issubclass(sender, ApplicationSubmission):
        submission_attachment_path = f"submission/{instance.id}"

        delete_directory(submission_attachment_path)
