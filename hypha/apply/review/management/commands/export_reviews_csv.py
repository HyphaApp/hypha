import csv

from django.core.management.base import BaseCommand

from opentech.apply.review.models import Review


class Command(BaseCommand):
    help = "Export reviews stats to a csv file.."

    def handle(self, *args, **options):
        with open('export_reviews.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
            writer.writerow(['Review author', 'Reviewer type', 'Review date', 'Submission', 'Submission date', 'Round/Lab/Fellowship'])
            for review in Review.objects.submitted():
                if review.submission.round:
                    submission_type = review.submission.round
                else:
                    submission_type = review.submission.page

                if review.author.reviewer.is_apply_staff:
                    reviewer_type = 'Staff'
                elif review.author.reviewer.is_reviewer:
                    reviewer_type = 'Reviewer'
                elif review.author.reviewer.is_partner:
                    reviewer_type = 'Partner'
                elif review.author.reviewer.is_community_reviewer:
                    reviewer_type = 'Community'

                writer.writerow([review.author, reviewer_type, review.created_at.strftime('%Y-%m-%d'), review.submission.title, review.submission.submit_time.strftime('%Y-%m-%d'), submission_type])
