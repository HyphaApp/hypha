import argparse
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.workflow import DRAFT_STATE


def check_not_negative(value) -> int:
    """Used to validate `older_than_days` argument

    Args:
        value: Argument to be validated

    Returns:
        int: Valid non-negative value

    Raises:
        argparse.ArgumentTypeError: if not non-negative integer
    """
    try:
        ivalue = int(value)
    except ValueError:
        ivalue = -1

    if ivalue < 0:
        raise argparse.ArgumentTypeError(
            f'"{value}" is an invalid non-negative integer value'
        )
    return ivalue


class Command(BaseCommand):
    help = (
        "Delete all drafts that haven't been modified in the specified time (in days)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "older_than_days",
            action="store",
            type=check_not_negative,
            help="Time in days to delete drafts older than",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not prompt the user for confirmation",
            required=False,
        )

    @transaction.atomic
    def handle(self, *args, **options):
        interactive = options["interactive"]
        older_than = options["older_than_days"]

        older_than_date = timezone.now() - timedelta(days=older_than)

        old_drafts = ApplicationSubmission.objects.filter(
            status=DRAFT_STATE, draft_revision__timestamp__date__lte=older_than_date
        )

        draft_count = old_drafts.count()

        if not (draft_count := old_drafts.count()):
            self.stdout.write(
                f"No drafts older than {older_than} day{'s' if older_than > 1 else ''} exist."
            )
            return

        if interactive:
            confirm = input(
                f"This action will permanently delete {draft_count} draft{'s' if draft_count != 1 else ''}.\nAre you sure you want to do this?\n\nType 'yes' to continue, or 'no' to cancel: "
            )
        else:
            confirm = "yes"

        if confirm == "yes":
            old_drafts.delete()
            self.stdout.write(
                f"{draft_count} draft{'s' if draft_count != 1 else ''} deleted."
            )
        else:
            self.stdout.write("Deletion cancelled.")
