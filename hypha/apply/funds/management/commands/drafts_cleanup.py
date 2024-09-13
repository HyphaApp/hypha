from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.funds.workflow import DRAFT_STATE


class Command(BaseCommand):
    help = "Delete all drafts that are older than 2 years"

    @transaction.atomic
    def handle(self, *args, **options):
        two_years_ago = timezone.now() - timedelta(days=730)

        old_drafts = ApplicationSubmission.objects.filter(
            status=DRAFT_STATE, submit_time__date__lte=two_years_ago
        )

        for draft in old_drafts:
            draft.delete()
