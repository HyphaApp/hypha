import csv

from django.core.management.base import BaseCommand

from hypha.apply.funds.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Export submission stats to a csv file."

    def handle(self, *args, **options):
        with open('export_submissions.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(['Submission ID', 'Submission title', 'Submission author', 'Submission e-mail', 'Submission value', 'Submission duration', 'Submission stage', 'Submission phase', 'Submission screening', 'Submission date', 'Submission region', 'Submission country', 'Round/Lab/Fellowship'])
            for submission in ApplicationSubmission.objects.all():
                submission.region = ''
                submission.country = ''
                for field_id in submission.question_text_field_ids:
                    if field_id not in submission.named_blocks:
                        question_field = submission.serialize(field_id)
                        name = question_field['question']
                        answer = str(question_field['answer'][0])
                        if answer and not answer == 'N':
                            if name == 'Region':
                                submission.region = answer
                            elif name == 'Country':
                                submission.country = answer

                if submission.round:
                    submission_type = submission.round
                else:
                    submission_type = submission.page

                try:
                    value = submission.value
                except KeyError:
                    value = 0

                writer.writerow([submission.id, submission.title, submission.full_name, submission.email, value, submission.duration, submission.stage, submission.phase, submission.screening_status, submission.submit_time.strftime('%Y-%m-%d'), submission.region, submission.country, submission_type])
