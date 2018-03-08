import argparse
import json

from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.funds.models import ApplicationSubmission, FundType, Round

User = get_user_model()

STREAMFIELD_MAP = {
    "field_application_name": "name",
    "field_application_mail": "email",
    "field_application_preapplied": "49a0f5f4-e8e9-4dfc-8575-205ee9675032",
    "field_application_apply_for": "c1277029-1718-40e3-8bf5-d80ece7fd343",
    "field_application_amount": "value",
    "field_application_amount_text": "value",
    "field_application_service": "ebdf9a22-58c7-4bd6-a58d-e71363357470",
    "field_application_service_other": "c8c329c7-78e4-4cbf-a3b1-77a1324e92ff",
    "field_application_duration3": "806d401c-b52c-46f7-9e96-f36fa70f53d8",
    "field_application_who": "1ec16cdc-7a68-40be-b17b-9a218def4260",
    "field_application_how": "4fa2ac11-d1cd-4d23-8082-93a14c8f99c8",
    "field_application_sustainability": "3cde39ae-b687-4c4f-b58b-849396c2fdb8",
    "field_application_dates": "0b2a4653-b390-44a6-b92e-fae4647e7ec4",
    "field_application_why": "6d75e412-cf53-4833-9f1d-3e0126512fb9",
    "field_application_why_rapiid": "1b181d1e-ef91-41af-b9c1-d096a991314b",
    "field_application_focus": "efd91eaf-378f-4aab-96cb-c5601155cbee",
    "field_application_objectives": "4be0c7bd-231d-4d9f-bd47-8589fc005f54",
    "field_application_beneficiaries": "6e0293ee-218e-4c3b-b82d-5bf91fdb21c9",
    "field_term_region": "6ff029c6-c6d1-4c37-a49a-46181b1cd33d",
    "field_application_problems": "7fb1001e-d458-414f-a5bb-006db6f89baf",
    "field_application_budget": "45d7d38a-9c9d-4c43-98df-bb95d4a1dd77",
    "field_application_legal_name": "632065c5-860f-4751-9b31-52914d7c6448",
    "field_application_contact": "13bb0d64-65f3-4340-8e7e-e5da80d706d5",
    "field_application_phone": "2cb9fe4b-df45-4181-80e5-14382f853081",
    "field_application_address": "bd29eb88-9754-4305-9b2d-406a875ec56a",
    "field_concept_upload": "607daeba-1f33-4ad0-b135-eda743ba8e3a",
    "field_application_otf_mission": "e695f0d7-4c74-4cc6-853f-bd62ecd19d3d",
    "field_application_otf_tos": "f40d1acc-d802-4cc6-b0e9-fff78dc54223",
    "field_application_otf_represent": "0b3c0827-38e2-439b-bca5-735835af1019",
    "field_application_otf_license": "bc9c960e-a6f4-4bc2-b626-efb5bc5552c6",
    "field_application_otf_complete": "5812b66d-630e-4ca2-8bea-819084278f55",
    "field_application_otf_deadline": "97d3746c-cf0f-449a-b3a3-7a9cdd45cc6d",
    "field_application_otf_list": "fc3d2a87-1151-418b-b1cd-9289f00bde35",
    "field_application_otf_newsletter": "83ecc69a-f47c-495e-bc8f-326e55aed67a",
}

FUND = FundType.objects.get(title='Rapid Response')
ROUND = Round.objects.get(title='Rapid Response open round')


class Command(BaseCommand):
    help = "Rapid response migration script. Requires a source JSON file."
    data = []

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            self.data = json.load(json_data)

            for id in self.data:
                self.process(id)

    def process(self, id):
        node = self.data[id]

        try:
            submission = ApplicationSubmission.objects.get(drupal_id=node['nid'])
        except ApplicationSubmission.DoesNotExist:
            submission = ApplicationSubmission(name=node['title'], drupal_id=node['nid'])

        # TODO timezone?
        submission.submit_time = datetime.utcfromtimestamp(node['created'])
        submission.user = self.get_user(node['uid'])

        submission.page = FUND
        submission.round = ROUND

        for field in node:
            if not field in STREAMFIELD_MAP:
                continue

            id = STREAMFIELD_MAP[field]
            submission.form_data[id] = self.get_field_value(field)
        submission.save()

    def get_user(self, uid):
        try:
            return User.objects.get(drupal_id=uid)
        finally:
            return None


    def get_field_value(self, field):
        """
        Handles the following formats:
        field: {(safe_)value: VALUE}
        field: {target_id: ID} -- Drupal ForeignKey. Reference to other node or user entities.
        field: {tid: ID} -- or term ID. fk to Categories
        field: []
        field: [{value|target_id|tid: VALUE},]
        """
        return ''

    def get_referenced_node(self, nid):
        pass

    def get_referenced_term(self, tid):
        pass

    def get_workflow_state(self):
        """
        workbench_moderation: {'current': {'state': STATE, 'timestamp': TS}}
        """
        pass
