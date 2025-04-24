import argparse
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from hypha.apply.funds.models.utils import SubmissionExportManager


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
    help = "Delete all generated exports older than the specified time (in days)"

    def add_arguments(self, parser):
        parser.add_argument(
            "older_than_days",
            action="store",
            type=check_not_negative,
            help="Time in days to delete exports older than",
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

        old_exports = SubmissionExportManager.objects.filter(
            created_time__lte=older_than_date
        )

        export_count = old_exports.count()

        if not export_count:
            self.stdout.write(
                f"No exports older than {older_than} day{'s' if older_than > 1 else ''} exist."
            )
            return

        if interactive:
            confirm = input(
                f"This action will permanently delete {export_count} generated export{'s' if export_count != 1 else ''}.\nAre you sure you want to do this?\n\nType 'yes' to continue, or 'no' to cancel: "
            )
        else:
            confirm = "yes"

        if confirm == "yes":
            old_exports.delete()
            self.stdout.write(
                f"{export_count} generate export{'s' if export_count != 1 else ''} deleted."
            )
        else:
            self.stdout.write("Deletion cancelled.")
