import csv

from django.core.management.base import BaseCommand

from opentech.apply.funds.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Export submission stats to a csv file."

    def handle(self, *args, **options):
        with open('export_submissions.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(['Submission title', 'Submission author', 'Submission e-mail', 'Submission value', 'Submission duration', 'Submission stage', 'Submission phase', 'Submission screening', 'Submission date', 'Round/Lab/Fellowship'])
            for submission in ApplicationSubmission.objects.all():
                if submission.round:
                    submission_type = submission.round
                else:
                    submission_type = submission.page

                try:
                    value = submission.value
                except KeyError:
                    value = 0

                writer.writerow([submission.title, submission.full_name, submission.email, value, submission.duration, submission.stage, submission.phase, submission.screening_status, submission.submit_time.strftime('%Y-%m-%d'), submission_type])
