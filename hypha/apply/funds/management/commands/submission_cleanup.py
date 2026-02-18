import argparse
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.workflows import DRAFT_STATE


def check_not_negative_or_zero(value) -> int:
    """Used to validate a provided days argument

    Args:
        value: Argument to be validated

    Returns:
        int: value that is > 0

    Raises:
        argparse.ArgumentTypeError: if not non-negative integer or 0
    """
    try:
        ivalue = int(value)
    except ValueError:
        ivalue = -1

    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            f'"{value}" is an invalid non-negative integer value'
        )
    return ivalue


class Command(BaseCommand):
    help = "Clean up submissions by deleting or anonymizing them. NOTE: Drafts will only be deleted if specified."

    def add_arguments(self, parser):
        parser.add_argument(
            "--drafts",
            action="store",
            type=check_not_negative_or_zero,
            help="Delete drafts that were created before the provided day threshold",
            required=False,
        )

        parser.add_argument(
            "--submissions",
            action="store",
            type=check_not_negative_or_zero,
            help="Anonymize submissions that haven't seen activity after the provided day threshold",
            required=False,
        )

        parser.add_argument(
            "--delete",
            action="store_false",
            dest="interactive",
            help="Delete submissions instead of anonymizing them. NOTE: Drafts will always be deleted, not anonymized",
        )

        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not prompt the user for confirmation",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        interactive = options["interactive"]

        if not options["drafts"] and not options["submissions"]:
            self.stdout.write(
                "Please use either --drafts [days] OR --submissions [days]"
            )

        if drafts_time_threshold := options["drafts"]:
            older_than_date = timezone.now() - timedelta(days=drafts_time_threshold)

            old_drafts = ApplicationSubmission.objects.filter(
                status=DRAFT_STATE, draft_revision__timestamp__date__lte=older_than_date
            )

            if draft_count := old_drafts.count():
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
                    self.stdout.write("Draft deletion cancelled.")
            else:
                self.stdout.write(
                    f"No drafts older than {drafts_time_threshold} day{'s' if drafts_time_threshold > 1 else ''} exist. Skipping!"
                )

        if sub_time_threshold := options["submissions"]:
            older_than_date = timezone.now() - timedelta(days=sub_time_threshold)

            old_subs = (
                ApplicationSubmission.objects.with_latest_update()
                .filter(last_update__date__lte=older_than_date)
                .exclude(status=DRAFT_STATE)
            )

            if sub_count := old_subs.count():
                if interactive:
                    confirm = input(
                        f"This action will permanently anonymize {sub_count} submission{'s' if sub_count != 1 else ''}.\nAre you sure you want to do this?\n\nType 'yes' to continue, or 'no' to cancel: "
                    )
                else:
                    confirm = "yes"

                if confirm == "yes":
                    old_subs.delete()
                    self.stdout.write(
                        f"{sub_count} submission{'s' if sub_count != 1 else ''} anonymized."
                    )
                else:
                    self.stdout.write("Submission deletion cancelled.")
            else:
                self.stdout.write(
                    f"No submissions older than {sub_time_threshold} day{'s' if sub_time_threshold > 1 else ''} exist. Skipping!"
                )
