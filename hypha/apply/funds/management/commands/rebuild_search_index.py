from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from hypha.apply.funds.models.submissions import ApplicationSubmission

CHUNK_SIZE = 500


class Command(BaseCommand):
    help = "Rebuild the full text search index (search_document) for all submissions."

    def handle(self, *args, **options):
        # Only load what prepare_search_vector() needs. This also keeps the
        # command safe to run from migration 0140, before later schema changes.
        self.submissions = ApplicationSubmission.objects.only(
            "id", "public_id", "form_data", "form_fields"
        )
        pks = list(
            ApplicationSubmission.objects.order_by("pk").values_list("pk", flat=True)
        )
        total = len(pks)
        self.failed = []
        indexed = 0

        for start in range(0, total, CHUNK_SIZE):
            chunk = []
            for submission in self.load_chunk(pks[start : start + CHUNK_SIZE]):
                try:
                    submission.search_document = submission.prepare_search_vector()
                except Exception as e:
                    self.report_failure(submission.pk, e)
                else:
                    chunk.append(submission)

            indexed += self.save_chunk(chunk)
            processed = min(start + CHUNK_SIZE, total)
            self.stdout.write(f"Processed {processed}/{total} submissions")

        self.stdout.write(
            self.style.SUCCESS(f"Rebuilt search index for {indexed} submissions.")
        )
        if self.failed:
            pks = ", ".join(str(pk) for pk in self.failed)
            self.stderr.write(
                self.style.ERROR(
                    f"Could not index {len(self.failed)} of {total} submissions: {pks}"
                )
            )

    def load_chunk(self, pks):
        """
        Load the whole chunk in one query. Form data is deserialized while
        loading, if that fails (e.g. a block type that no longer exists) load
        row by row to find the culprits.
        """
        try:
            return list(self.submissions.filter(pk__in=pks))
        except Exception:
            pass

        loaded = []
        for pk in pks:
            try:
                loaded.extend(self.submissions.filter(pk=pk))
            except Exception as e:
                self.report_failure(pk, e)
        return loaded

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
