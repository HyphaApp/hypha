import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from hypha.apply.funds.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Export applications of a specific round to a csv file."

    def add_arguments(self, parser):
        parser.add_argument('round_name', type=str)
        parser.add_argument('round_id', type=int)


    def handle(self, *args, **options):
        base_path = os.path.join(settings.PROJECT_DIR,'../media')
        filename = options['round_name'] + '_applciations_data.csv'
        with open(os.path.join(base_path+'/'+filename), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            header_row = []
            values = []
            check = False
            index = 0

            for submission in ApplicationSubmission.objects.filter(round=options['round_id']):
                for field_id in submission.question_text_field_ids:
                    question_field = submission.serialize(field_id)
                    field_name = question_field['question']
                    field_value = question_field['answer']
                    if field_id not in submission.named_blocks:
                        header_row.append(field_name) if not check else header_row
                        values.append(field_value)
                    else:
                        header_row.insert(index,field_name) if not check else header_row
                        values.insert(index,field_value)
                        index = index + 1
                        
                if not check:
                    writer.writerow(header_row)
                    self.intial_header_length = len(header_row)
                    check = True
                
                writer.writerow(values)
                values.clear()
                index = 0

        return base_path + '/' + filename
