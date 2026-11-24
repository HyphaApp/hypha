import sys
from functools import partial

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from hypha.apply.funds.models.application_revisions import ApplicationRevision
from hypha.apply.funds.models.mixins import AccessFormData
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.utils import delete_directory


def revision_files_to_delete(revision):
    """
    Files of the revision that no other revision or the submission uses.

    Files kept between edits are not copied, revisions share them.
    """
    submission = revision.submission
    others = [submission, *submission.revisions.exclude(pk=revision.pk)]
    in_use = set()
    for other in others:
        for value in other.extract_files().values():
            in_use |= AccessFormData._file_names(value)

    files = []
    for value in revision.extract_files().values():
        for file in value if isinstance(value, list) else [value]:
            if file and file.name not in in_use:
                files.append(file)
    return files


def delete_revision_files(revision):
    """
    Delete the files only the deleted revision used.

    Revisions are mostly deleted together with their submission, then its whole
    folder is removed and there is nothing to check.
    """
    if not ApplicationSubmission.objects.filter(pk=revision.submission_id).exists():
        return
    for file in revision_files_to_delete(revision):
        file.delete()


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
        # Only after commit is it known if the submission was deleted as well.
        transaction.on_commit(partial(delete_revision_files, instance))
    elif issubclass(sender, ApplicationSubmission):
        submission_attachment_path = f"submission/{instance.id}"

        if default_storage.exists(submission_attachment_path):
            delete_directory(submission_attachment_path)
