import argparse
import json

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from opentech.apply.funds.models import ApplicationSubmission, Round, LabType
from opentech.apply.funds.models.forms import RoundBaseReviewForm, LabBaseReviewForm
from opentech.apply.review.models import Review
from opentech.apply.review.options import NA


class MigrateCommand(BaseCommand):
    help = "Review migration script. Requires a source JSON file."
    data = []

    REVIEWFIELD_MAP = {
        "community_lab_review": {
            "submission": "field_review_community_lab",
            "recommendation": "field_clr_recommendation",
            "rec_map": {
                "1": 2,
                "0": 0,
            },
        },
        "concept_note_review": {
            "submission": "field_review_concept_note",
            "recommendation": "field_pr_recommendation",
            "rec_map": {
                "2": 1,
                "1": 2,
                "0": 0,
            },
        },
        "proposal_review": {
            "submission": "field_review_proposal",
            "recommendation": "field_pr_recommendation",
            "rec_map": {
                "2": 1,
                "1": 2,
                "0": 0,
            },
        },
        "fellowship_application_review": {
            "submission": "field_review_fellowship_app",
            "recommendation": "field_fr_overall_rate",
            "rec_map": {
                "5": 2,
                "4": 2,
                "3": 1,
                "2": 0,
                "1": 0,
            },
        },
        "fellowship_proposal_review": {
            "submission": "field_review_fellowship",
            "recommendation": "field_fr_overall_rate",
            "rec_map": {
                "5": 2,
                "4": 2,
                "3": 1,
                "2": 0,
                "1": 0,
            },
        },
        "rapid_response_review": {
            "submission": "field_review_rapid_response",
            "recommendation": "field_rrr_recommend",
            "rec_map": {
                "3": 2,
                "2": 1,
                "1": 0,
            },
        },
    }

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            self.data = json.load(json_data)

            # A user can only submitt a single review in the new system so pick the latest one.
            blacklist = {"7574", "7413", "7412", "5270", "6468", "6436", "5511", "3490", "2840", "2837", "2737", "9362", "9203", "8958", "13313", "4868", "4867", "5863", "5770", "3962", "3747"}

            counter = 0
            for id in self.data:
                if id not in blacklist:
                    self.process(id)
                    counter += 1

            self.stdout.write(f"Imported {counter} reviews.")

    def process(self, id):
        node = self.data[id]

        try:
            review = Review.objects.get(drupal_id=node['nid'])
        except Review.DoesNotExist:
            review = Review(drupal_id=node['nid'])

        # Disable auto_* on date fields so imported dates are used.
        for field in review._meta.local_fields:
            if field.name == "created_at":
                field.auto_now_add = False
            elif field.name == "updated_at":
                field.auto_now = False

        # TODO timezone?
        review.created_at = datetime.fromtimestamp(int(node['created']), timezone.utc)
        review.updated_at = datetime.fromtimestamp(int(node['changed']), timezone.utc)
        review.author = self.get_user(node['uid'])
        review.recommendation = self.get_recommendation(node)
        review.submission = self.get_submission(node)
        review.revision = review.submission.live_revision

        if self.CONTENT_TYPE == "fund":
            ROUND = Round.objects.get(title=self.ROUND_NAME)
            if self.APPLICATION_TYPE == "request":
                FORM = RoundBaseReviewForm.objects.get(round=ROUND)
            elif self.APPLICATION_TYPE == "concept":
                FORM = RoundBaseReviewForm.objects.filter(round=ROUND)[0]
            elif self.APPLICATION_TYPE == "proposal":
                FORM = RoundBaseReviewForm.objects.filter(round=ROUND)[1]
            review.form_fields = FORM.form.form_fields
        elif self.CONTENT_TYPE == "lab":
            LAB = LabType.objects.get(title=self.LAB_NAME)
            FORM = LabBaseReviewForm.objects.get(lab=LAB)
            review.form_fields = FORM.form.form_fields

        form_data = {}

        for field in node:
            if field in self.STREAMFIELD_MAP:
                try:
                    id = self.STREAMFIELD_MAP[field]['id']
                    form_data[id] = self.get_field_value(field, node)
                except TypeError:
                    pass

        if "comments" not in form_data or not form_data["comments"]:
            form_data["comments"] = "No comment."

        form_data["recommendation"] = review.recommendation

        review.form_data = form_data

        scores = [review.data(field.id)[1] for field in review.score_fields if review.data(field.id)[1] != NA]
        try:
            review.score = sum(scores) / len(scores)
        except ZeroDivisionError:
            review.score = 0

        try:
            review.save()
            self.stdout.write(f"Processed \"{node['title']}\" ({node['nid']})")
        except IntegrityError:
            self.stdout.write(f"*** Skipped \"{node['title']}\" ({node['nid']}) due to IntegrityError")

    def get_user(self, uid):
        try:
            User = get_user_model()
            return User.objects.get(drupal_id=uid)
        except User.DoesNotExist:
            return None

    def get_field_value(self, field, node):
        """
        Handles the following formats:
        field: {(safe_)value: VALUE}
        field: {target_id: ID} -- Drupal ForeignKey. Reference to other node or user entities.
        field: {tid: ID} -- or term ID. fk to Categories
        field: []
        field: [{value|target_id|tid: VALUE},]
        """
        mapping = self.STREAMFIELD_MAP[field]
        mapping_type = mapping['type']
        key = mapping.get('key', 'value')
        source_value = node[field]
        value = None

        if mapping_type == "direct":
            value = source_value
        elif mapping_type == 'value':
            if key in source_value:
                value = self.nl2br(source_value[key]) if source_value else ''
            else:
                value = self.nl2br(source_value['value']) if source_value else ''
        elif mapping_type == 'merge_value':
            values = []
            i = 0
            for item in source_value:
                question = self.REQUEST_QUESTION_MAP[node['request_nid']]
                if i in question:
                    values.append(f"<strong>{question[i]}</strong>{item[key]}<br>\n")
                i += 1
            merged_values = ''.join(values)
            value = self.nl2br(merged_values) if source_value else ''
        elif mapping_type == 'score':
            value_rate = int(source_value[key]) if source_value else NA
            value_text = ''
            if "_rate" in field:
                field = field.replace('field_field_', 'field_')
                text_field = field[:-5]
                if text_field in self.STREAMFIELD_MAP:
                    value_text_field = node[text_field]
                    if 'safe_value' in value_text_field:
                        value_text = self.nl2br(value_text_field['safe_value']) if value_text_field else ''
                    else:
                        value_text = self.nl2br(value_text_field['value']) if value_text_field else ''
            value = [value_text, value_rate]
        elif mapping_type == 'map' and 'map' in 'mapping':
            value = mapping['map'].get(source_value[key])
        elif mapping_type == 'boolean':
            value = source_value[key] == '1' if source_value else False

        return value

    def get_recommendation(self, node):
        mapping = self.REVIEWFIELD_MAP[node['type']]
        field_name = mapping['recommendation']
        rec_map = mapping.get('rec_map')
        try:
            return rec_map[node[field_name]['value']]
        except TypeError:
            return 0

    def get_submission(self, node):
        mapping = self.REVIEWFIELD_MAP[node['type']]
        field_name = mapping['submission']
        try:
            nid = node[field_name]['target_id']
            return ApplicationSubmission.objects.get(drupal_id=nid)
        except ApplicationSubmission.DoesNotExist:
            return None

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')
