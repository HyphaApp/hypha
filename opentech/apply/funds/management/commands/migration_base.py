import argparse
import json

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError
from django_fsm import FSMField

from opentech.apply.categories.models import Category, Option
from opentech.apply.categories.categories_seed import CATEGORIES
from opentech.apply.funds.models import ApplicationSubmission, FundType, Round, LabType
from opentech.apply.funds.models.forms import RoundBaseForm, LabBaseForm
from opentech.apply.funds.workflow import INITIAL_STATE


class MigrateCommand(BaseCommand):
    help = "Application migration script. Requires a source JSON file."
    data = []
    terms = {}

    # Monkey patch the status field so it is no longer protected
    patched_status_field = FSMField(default=INITIAL_STATE, protected=False)
    setattr(ApplicationSubmission, 'status', patched_status_field)

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        # Prepare the list of categories.
        for item in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=item['category'])
            option, _ = Option.objects.get_or_create(value=item['name'], category=category)
            self.terms[item['tid']] = option

        with options['source'] as json_data:
            self.data = json.load(json_data)

            counter = 0
            for id in self.data:
                self.process(id)
                counter += 1

            self.stdout.write(f"Imported {counter} submissions.")

    def process(self, id):
        node = self.data[id]

        try:
            submission = ApplicationSubmission.objects.get(drupal_id=node['nid'])
        except ApplicationSubmission.DoesNotExist:
            submission = ApplicationSubmission(drupal_id=node['nid'])

        # TODO timezone?
        submission.submit_time = datetime.fromtimestamp(int(node['created']), timezone.utc)
        submission.user = self.get_user(node['uid'])

        if self.CONTENT_TYPE == "fund":
            FUND = FundType.objects.get(title=self.FUND_NAME)
            submission.page = FUND
            ROUND = Round.objects.get(title=self.ROUND_NAME)
            submission.round = ROUND
            if self.APPLICATION_TYPE == "request":
                FORM = RoundBaseForm.objects.get(round=ROUND)
            elif self.APPLICATION_TYPE == "concept":
                FORM = RoundBaseForm.objects.filter(round=ROUND)[0]
            elif self.APPLICATION_TYPE == "proposal":
                FORM = RoundBaseForm.objects.filter(round=ROUND)[1]
            submission.form_fields = FORM.form.form_fields
        elif self.CONTENT_TYPE == "lab":
            LAB = LabType.objects.get(title=self.LAB_NAME)
            submission.page = LAB
            FORM = LabBaseForm.objects.get(lab=LAB)
            submission.form_fields = FORM.form.form_fields

        submission.status = self.get_workflow_state(node)

        if 'proposal_nid' in node:
            try:
                submission.next = ApplicationSubmission.objects.get(drupal_id=node['proposal_nid'])
            except ApplicationSubmission.DoesNotExist:
                self.stdout.write("No related proposal found, please import proposals before applications.")
                pass

        form_data = {
            'skip_account_creation_notification': True,
        }

        for field in node:
            if field in self.STREAMFIELD_MAP:
                try:
                    id = self.STREAMFIELD_MAP[field]['id']
                    form_data[id] = self.get_field_value(field, node)
                except TypeError:
                    pass

        if "value" not in form_data:
            form_data["value"] = 0

        if "duration" not in form_data or not form_data["duration"]:
            form_data["duration"] = "1"

        if "email" not in form_data or not form_data["email"]:
            if hasattr(submission.user, 'email'):
                form_data["email"] = submission.user.email
            else:
                form_data["email"] = f"user+{node['uid']}@exeample.com"

        submission.form_data = form_data

        try:
            submission.save()
            self.stdout.write(f"Processed \"{node['title']}\" ({node['nid']})")
        except IntegrityError:
            self.stdout.write(f"*** Skipped \"{node['title']}\" ({node['nid']}) due to IntegrityError")
            pass

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
                question = self.REQUEST_QUESTION_MAP[node['field_application_request']['target_id']]
                values.append(f"<strong>{question[i]}</strong>{item[key]}<br>\n")
                i += 1
            merged_values = ''.join(values)
            value = self.nl2br(merged_values) if source_value else ''
        elif mapping_type == 'map' and 'map' in 'mapping':
            value = mapping['map'].get(source_value[key])
        elif mapping_type == 'address' and 'map' in mapping:
            try:
                value_map = mapping['map']
                value = {}
                for item in value_map:
                    value[value_map[item]] = source_value[item]
                value = json.dumps(value)
            except TypeError:
                value = {}
        elif mapping_type == 'boolean':
            value = source_value[key] == '1' if source_value else False
        elif mapping_type == 'category':
            if not source_value:
                value = []
            else:
                if isinstance(source_value, dict):
                    option = self.get_referenced_term(source_value[key])
                    value = [option] if option else []
                else:
                    value = []
                    for item in source_value:
                        option = self.get_referenced_term(item[key])
                        if option:
                            value.append(option)
        elif mapping_type == 'file':
            # TODO finish mapping. Requires access to the files.
            value = {}

        return value

    def get_referenced_term(self, tid):
        try:
            term = self.terms[tid]
            return term.id
        except KeyError:
            return None

    def get_referenced_node(self, nid):
        pass

    def get_workflow_state(self, node):
        """
        workbench_moderation: {'current': {'state': STATE, 'timestamp': TS}}
        """
        states_request = {
            "draft": "in_discussion",
            "published": "in_discussion",
            "in_discussion": "in_discussion",
            "council_review": "internal_review",
            "ready_for_reply": "post_review_discussion",
            "contract_review": "post_review_discussion",
            "in_contract": "accepted",
            "invited_for_proposal": "accepted",
            "dropped_concept_note": "rejected",
            "dropped": "rejected",
            "dropped_without_review": "rejected"
        }

        states_concept = {
            "draft": "in_discussion",
            "published": "in_discussion",
            "in_discussion": "in_discussion",
            "council_review": "concept_internal_review",
            "ready_for_reply": "concept_review_discussion",
            "contract_review": "concept_review_discussion",
            "in_contract": "invited_to_proposal",
            "invited_for_proposal": "invited_to_proposal",
            "dropped_concept_note": "concept_rejected",
            "dropped": "concept_rejected",
            "dropped_without_review": "concept_rejected"
        }

        states_proposal = {
            "draft": "draft_proposal",
            "published": "proposal_discussion",
            "in_discussion": "proposal_discussion",
            "council_review": "external_review",
            "ready_for_reply": "proposal_more_info",
            "contract_review": "post_external_review_discussion",
            "in_contract": "proposal_accepted",
            "invited_for_proposal": "proposal_accepted",
            "dropped_concept_note": "proposal_rejected",
            "dropped": "proposal_rejected",
            "dropped_without_review": "proposal_rejected"
        }

        if self.APPLICATION_TYPE == "request":
            workflow_state = states_request.get(node['workbench_moderation']['current']['state'], "in_discussion")
        elif self.APPLICATION_TYPE == "concept":
            workflow_state = states_concept.get(node['workbench_moderation']['current']['state'], "in_discussion")
        elif self.APPLICATION_TYPE == "proposal":
            workflow_state = states_proposal.get(node['workbench_moderation']['current']['state'], "draft_proposal")
        else:
            workflow_state = None

        return workflow_state

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')
