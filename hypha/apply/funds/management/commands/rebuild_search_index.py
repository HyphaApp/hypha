from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from hypha.apply.funds.models.submissions import ApplicationSubmission

CHUNK_SIZE = 500


class Command(BaseCommand):
    help = "Rebuild the full text search index (search_document) for all submissions."

    def handle(self, *args, **options):
        submissions = ApplicationSubmission.objects.defer("search_document").order_by(
            "pk"
        )
        total = submissions.count()
        self.failed = []
        indexed = 0
        processed = 0
        chunk = []

        for submission in submissions.iterator(chunk_size=CHUNK_SIZE):
            processed += 1
            try:
                submission.search_document = submission.prepare_search_vector()
            except Exception as e:
                self.report_failure(submission.pk, e)
            else:
                chunk.append(submission)

            if len(chunk) >= CHUNK_SIZE:
                indexed += self.save_chunk(chunk)
                chunk = []
            if processed % CHUNK_SIZE == 0:
                self.stdout.write(f"Processed {processed}/{total} submissions")

        if chunk:
            indexed += self.save_chunk(chunk)

        self.stdout.write(
            self.style.SUCCESS(f"Rebuilt search index for {indexed} submissions.")
        )
        if self.failed:
            pks = ", ".join(str(pk) for pk in self.failed)
            self.stderr.write(
                self.style.ERROR(
                    f"Could not index {len(self.failed)} submissions: {pks}"
                )
            )

    def save_chunk(self, chunk):
        """
        Save the whole chunk in one query. If the database rejects it (e.g. a
        tsvector over the size limit) save row by row to find the culprits.
        """
        try:
            with transaction.atomic():
                ApplicationSubmission.objects.bulk_update(chunk, ["search_document"])
            return len(chunk)
        except DatabaseError:
            pass

        saved = 0
        for submission in chunk:
            try:
                with transaction.atomic():
                    ApplicationSubmission.objects.filter(pk=submission.pk).update(
                        search_document=submission.search_document
                    )
                saved += 1
            except DatabaseError as e:
                self.report_failure(submission.pk, e)
        return saved

    def report_failure(self, pk, error):
        self.failed.append(pk)
        self.stderr.write(
            self.style.WARNING(f"Could not index submission {pk}: {error}")
        )
