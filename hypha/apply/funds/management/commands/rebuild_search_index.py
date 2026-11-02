from django.core.management.base import BaseCommand

from hypha.apply.funds.models.submissions import ApplicationSubmission


class Command(BaseCommand):
    help = "Rebuild the full text search index (search_document) for all submissions."

    def handle(self, *args, **options):
        submissions = ApplicationSubmission.objects.select_related("page", "round")
        total = submissions.count()
        for count, submission in enumerate(submissions.iterator(chunk_size=500), 1):
            ApplicationSubmission.objects.filter(pk=submission.pk).update(
                search_document=submission.prepare_search_vector()
            )
            if count % 500 == 0:
                self.stdout.write(f"Indexed {count}/{total} submissions")

        self.stdout.write(
            self.style.SUCCESS(f"Rebuilt search index for {total} submissions.")
        )
