import bleach
import json

from django.core.management.base import BaseCommand

from hypha.apply.funds.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Export submission stats to a json file."

    def handle(self, *args, **options):
        data = []

        data.append({
            'id': 'Submission ID',
            'title': 'Submission title',
            'author': 'Submission author',
            'mail': 'Submission e-mail',
            'value': 'Submission value',
            'duration': 'Submission duration',
            'reapplied': 'Submission reapplied',
            'stage': 'Submission stage',
            'phase': 'Submission phase',
            'screening': 'Submission screening',
            'date': 'Submission date',
            'region': 'Submission region',
            'country': 'Submission country',
            'focus': 'Submission focus',
            'round': 'Round/Lab/Fellowship',
            'do': 'What would you like to do with our support?',
            'work': 'Which best describes the type of work you will do?',
        })

        for submission in ApplicationSubmission.objects.all():
            submission_region = ''
            submission_country = ''
            submission_focus = ''
            submission_reapplied = ''
            submission_do = ''
            submission_work = ''
            try:
                if 'in scope' not in submission.screening_status.title.lower():
                    raise Exception()
                for field_id in submission.question_text_field_ids:
                    if field_id not in submission.named_blocks:
                        question_field = submission.serialize(field_id)
                        name = question_field['question']
                        if isinstance(question_field['answer'], str):
                            answer = question_field['answer']
                        else:
                            answer = ','.join(question_field['answer'])

                        if 'consent to us sharing some of your data' in name and not answer == 'True':
                            raise Exception()

                        if answer and not answer == 'N':
                            if 'which geographies' in name:
                                submission_region = answer
                            elif name == 'Country':
                                submission_country = answer
                            elif name == 'Focus':
                                submission_focus = answer
                            elif 'or received funding' in name:
                                submission_reapplied = answer
                            elif 'with our support' in name:
                                submission_do = bleach.clean(answer, strip=True)
                            elif 'type of work you' in name:
                                submission_work = answer
            except Exception:
                continue

            if submission.round:
                submission_type = submission.round
            else:
                submission_type = submission.page

            try:
                submission_value = submission.value
            except KeyError:
                submission_value = 0

            data.append({
                'id': submission.id,
                'title': submission.title,
                'author': submission.full_name,
                'mail': submission.email,
                'value': submission_value,
                'duration': submission.duration,
                'reapplied': submission_reapplied,
                'stage': str(submission.stage),
                'phase': str(submission.phase),
                'screening': str(submission.screening_status),
                'date': submission.submit_time.strftime('%Y-%m-%d'),
                'region': submission_region,
                'country': submission_country,
                'focus': submission_focus,
                'round': str(submission_type),
                'do': submission_do,
                'work': submission_work,
            })

        with open('export_public_submissions.json', 'w', newline='') as jsonfile:
            json.dump(data, jsonfile)
