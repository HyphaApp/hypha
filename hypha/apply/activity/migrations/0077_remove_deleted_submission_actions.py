from django.db import migrations

from hypha.apply.activity.messaging import MESSAGES
from hypha.apply.activity.models import Event
from hypha.apply.funds.models.submissions import ApplicationSubmission


def remove_submission_events_without_submission(apps, schema_editor):
    """ "
    Remove all NEW_SUBMISSION events that don't belong to a submission
    """

    # Pull all existing submission IDs
    all_application_ids = ApplicationSubmission.objects.all().values_list(
        "id", flat=True
    )

    # Filter events by NEW_SUBMISSION & exclude any event that has an object_id that exists in all_application_ids
    new_sub_events = Event.objects.filter(type=MESSAGES.NEW_SUBMISSION).exclude(
        object_id__in=all_application_ids
    )

    # Remove these events
    new_sub_events.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("activity", "0076_alter_event_type"),
    ]

    operations = [migrations.RunPython(remove_submission_events_without_submission)]
