import json

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.categories.models import Category
from opentech.apply.funds.models import ApplicationForm, FundType, Round
from opentech.apply.funds.models.forms import ApplicationBaseForm, ApplicationBaseReviewForm
from opentech.apply.review.models import ReviewForm

from opentech.apply.home.models import ApplyHomePage
from opentech.apply.users.groups import STAFF_GROUP_NAME

FS_ROUND_TITLE = 'Fellowship archive round'
FS_FUND_TITLE = 'Fellowship archive fund'


class Command(BaseCommand):
    help = "Pre-seeds the fellowship application and proposal form and fund type. Depends on the categories seed being run first."

    @transaction.atomic
    def handle(self, *args, **options):
        # There's an Internet Freedom Fund open round, so bail out. Avoids duplicate command runs.
        if Round.objects.filter(title=FS_ROUND_TITLE).count():
            self.stdout.write(self.style.WARNING('Skipping. The target Round/Fund Type and Application Form exist'))
            return

        application_form = self.create_fellowship_application_form()
        proposal_form = self.create_fellowship_proposal_form()
        application_review_form = self.create_fellowship_application_review_form()
        proposal_review_form = self.create_fellowship_proposal_review_form()
        fund = self.create_fellowship_fund_type(application_form, proposal_form, application_review_form, proposal_review_form)
        self.create_fellowship_round(fund)

    def create_fellowship_application_form(self):

        focus_id = Category.objects.get(name='Focus').id
        objectives_id = Category.objects.get(name='Objective(s)').id
        beneficiaries_id = Category.objects.get(name='Beneficiaries').id
        regions_id = Category.objects.get(name='Region(s)').id
        addressed_id = Category.objects.get(name='Addressed problems').id
        status_id = Category.objects.get(name='Project status').id

        data = [
            {"type": "text_markup", "value": "<h3>About you</h3>", "id": "ef672ec5-f24c-4e95-9f18-522a5a1e6833"},
            {"type": "title", "value": {"field_label": "What is your project name?", "help_text": "", "info": None}, "id": "32c37ee8-7d5b-4fc0-b606-9697a1c7e5c2"},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "3b051ef2-3c75-4a70-aae3-999d58852810"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "bfc488d3-b77d-427d-825d-9000797e9576"},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}, "id": "2c0db01a-b5ab-4882-aad8-8c9a2ec05e8f"},
            {"type": "value", "value": {"field_label": "If you are applying for direct funding, how much do you need?", "help_text": "Amount requested should be less than 50000 USD.", "info": None}, "id": "cfae89dc-f327-45f4-80e9-f267c3bd1ec7"},
            {"type": "char", "value": {"field_label": "What is your current or most recent position and employer or research institution?", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "1282223d-77f5-4047-be03-4df4c4b2148a"},
            {"type": "rich_text", "value": {"field_label": "What are (or were) your roles and responsibilities there?", "help_text": "", "required": "", "default_value": ""}, "id": "9c0256e4-42e1-41fe-9880-7f621d6c3458"},
            {"type": "dropdown", "value": {"field_label": "Have you ever applied or received funding through an OTF fellowship program?", "help_text": "", "required": "", "choices": ["Yes", "No"]}, "id": "f8efef0a-0632-4c81-b4db-7bc6a06caa7d"},
            {"type": "text_markup", "value": "<h3>About your project</h3>", "id": "3541d1b1-afc7-4dcd-8ed9-e9af27de5f3d"},
            {"type": "rich_text", "value": {"field_label": "What is your project idea?", "help_text": "", "required": "", "default_value": ""}, "id": "1eb8b4e3-e2bb-4810-a8ce-3fc82a3192c8"},
            {"type": "rich_text", "value": {"field_label": "How would you do it?", "help_text": "", "required": "", "default_value": ""}, "id": "177d56e8-2df1-4ead-8e3d-4916610fbed6"},
            {"type": "rich_text", "value": {"field_label": "Why are you the right person for this project?", "help_text": "", "required": "", "default_value": ""}, "id": "05ff1755-947b-4e41-8f71-aae99977c572"},
            {"type": "duration", "value": {"field_label": "How long do you want to work on this fellowship?", "help_text": "", "info": None}, "id": "3ccac109-2839-4b5d-b133-0e6cfca7c766"},
            {"type": "text_markup", "value": "<h3>Host organization</h3>", "id": "f4b3ae6f-a1d6-4c9d-b334-e40614167257"},
            {"type": "char", "value": {"field_label": "What is your most ideal host organization?", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "0afaf4e1-4556-4e79-aa3d-4990e33620da"},
            {"type": "char", "value": {"field_label": "What is your next best host organization?", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "a543b34f-ae6a-4b17-8ac3-ececc14573a0"},
            {"type": "text_markup", "value": "<h3>Request specific questions</h3>", "id": "755363fa-6a1c-422f-a03f-89db07a96e17"},
            {"type": "rich_text", "value": {"field_label": "Request specific questions", "help_text": "", "required": "", "default_value": ""}, "id": "57cc52e2-b3ff-4e9f-a5fe-42e7735e16c2"},
            {"type": "text_markup", "value": "<h3>Descriptors</h3>", "id": "b6ee65b3-d5cd-4cb0-9d7c-6e29d86deaaf"},
            {"type": "category", "value": {"field_label": "Status", "help_text": "", "required": "", "category": status_id, "multi": "true"}, "id": "ff4d12ff-7b88-4e87-bb5b-81543aef0e25"},
            {"type": "category", "value": {"field_label": "Objectives", "help_text": "", "required": "true", "category": objectives_id, "multi": "true"}, "id": "30c41288-a762-4003-acce-8c12e7343d90"},
            {"type": "category", "value": {"field_label": "Beneficiaries", "help_text": "", "required": "", "category": beneficiaries_id, "multi": "true"}, "id": "56833441-542b-4a06-8ad2-8e7e8fd1a334"},
            {"type": "category", "value": {"field_label": "Focus", "help_text": "", "required": "", "category": focus_id, "multi": "true"}, "id": "6b404851-ce2b-494f-b9f7-62858a937469"},
            {"type": "category", "value": {"field_label": "Addressed problems", "help_text": "", "required": "true", "category": addressed_id, "multi": "true"}, "id": "590e4b77-c4f4-4bd0-b5be-2ad2851da4f5"},
            {"type": "category", "value": {"field_label": "Region", "help_text": "", "required": "", "category": regions_id, "multi": "true"}, "id": "81c01278-8ba4-4d84-a1da-e05a07aad874"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "25740b9d-0f8f-4ce1-88fa-c6ee831c6aef"},
            {"type": "text_markup", "value": "<h3>I acknowledge</h3>", "id": "f69d3a56-491a-4321-89b7-4d7e34d69a1d"},
            {"type": "checkbox", "value": {"field_label": "My application will be dismissed if it does not fit within OTF\'s mission, values, principles statements.", "help_text": "", "default_value": ""}, "id": "5178e15f-d442-4d36-824d-a4292ef77062"},
            {"type": "text_markup", "value": "Read our <a href=\"\/about/program\">mission, values, and principles</a>.", "id": "b0c69627-d7db-4633-b46f-0e787dddc779"},
            {"type": "checkbox", "value": {"field_label": "I have read and understand OTF\'s Terms and Privacy policy.", "help_text": "", "default_value": ""}, "id": "bd91e220-4cdb-4392-8054-7b7dfe667d46"},
            {"type": "text_markup", "value": "Read the <a href=\"\/tos\">Terms and Privacy policy</a>.", "id": "6f6236fd-9d1d-4090-a819-72fb96205bc0"},
            {"type": "checkbox", "value": {"field_label": "I am legally able to sign contracts or represent an organization that can.", "help_text": "", "default_value": ""}, "id": "8d000129-ca8b-48cf-8dc2-4651bcbe46e8"},
            {"type": "checkbox", "value": {"field_label": "I understand that all intellectual property created with support for this application must be openly licensed.", "help_text": "", "default_value": ""}, "id": "92f0801e-b9dc-4edc-9716-3f1709ae1c9b"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is incomplete in any way, it will be dismissed.", "help_text": "", "default_value": ""}, "id": "3a3f2da3-4e32-4b86-9060-29c606927114"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is after a deadline, it will not be reviewed until after the next deadline.", "help_text": "", "default_value": ""}, "id": "19395179-ed9f-4556-9b6b-ab5caef4f610"},
            {"type": "text_markup", "value": "<h3>I would like to</h3>", "id": "21c9a554-d0d2-4543-9ca5-f53e506fb7c4"},
            {"type": "checkbox", "value": {"field_label": "Sign up to the OTF-Announce list, low traffic (funding opportunities, major alerts, etc).", "help_text": "", "default_value": ""}, "id": "1345a8eb-4dcc-4170-a5ac-edda42d4dafc"},
            {"type": "checkbox", "value": {"field_label": "Sign up for OTF\'s daily newsletter (collection of news related to global internet freedom).", "help_text": "", "default_value": ""}, "id": "4ca22ebb-daba-4fb6-a4a6-b130dc6311a8"}
        ]

        application_form, _ = ApplicationForm.objects.get_or_create(name='Fellowship application', defaults={'form_fields': json.dumps(data)})

        return application_form

    def create_fellowship_proposal_form(self):

        data2 = [
            {"type": "text_markup", "value": "<h3>Proposal information</h3>", "id": ""},
            {"type": "title", "value": {"field_label": "Proposal title", "help_text": "", "info": None}, "id": ""},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "c0c75948-b3c3-42be-8646-bc2a5d8521c3"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "a607ec56-da2a-46d4-b0c9-7c8f3c351a6e"},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}, "id": "8d3cf1ac-928f-4ee2-ad12-2e5fb16b4748"},
            {"type": "value", "value": {"field_label": "If you are applying for direct funding, how much do you need?", "help_text": "Amount requested should be less than 50000 USD.", "info": None}, "id": "cfae89dc-f327-45f4-80e9-f267c3bd1ec7"},
            {"type": "duration", "value": {"field_label": "How long do you want to work on this fellowship?", "help_text": "", "info": None}, "id": "08b9b5c3-e01d-41ac-95be-600a4fee7d87"},
            {"type": "char", "value": {"field_label": "Host organisation", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "bc03235e-3c78-4770-9fc2-97feb93c2c8c"},
            {"type": "date", "value": {"field_label": "Start date", "help_text": "", "required": "", "default_value": ""}, "id": "672cb6f1-335c-4005-a0f1-46c414feda06"},
            {"type": "date", "value": {"field_label": "Completion date", "help_text": "", "required": "", "default_value": ""}, "id": "8262f209-f084-4a79-9dfa-2d18137119bb"},
            {"type": "rich_text", "value": {"field_label": "Objectives", "help_text": "", "required": "", "default_value": ""}, "id": "af2c5f38-7257-4295-87fa-787060e845ef"},
            {"type": "rich_text", "value": {"field_label": "Milestones and dates", "help_text": "", "required": "", "default_value": ""}, "id": "3c521847-7642-4cae-aca9-d5336ad8962d"},
            {"type": "rich_text", "value": {"field_label": "Anticipated outputs and outcomes", "help_text": "", "required": "", "default_value": ""}, "id": "fd0eb7ea-e054-4bcf-9580-eb672d44745c"},
            {"type": "text_markup", "value": "<h3>Request specific questions</h3>", "id": "b05a54d1-3a59-41d1-bb70-d5f0f0acd67d"},
            {"type": "rich_text", "value": {"field_label": "Request specific questions", "help_text": "", "required": "", "default_value": ""}, "id": "b6d71932-98c2-4ce8-a5e6-454a1f800d21"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "30dfa46e-f656-46c9-9efc-bab9029f2008"}
        ]

        proposal_form, _ = ApplicationForm.objects.get_or_create(name='Fellowship proposal', defaults={'form_fields': json.dumps(data2)})

        return proposal_form

    def create_fellowship_application_review_form(self):

        data3 = [
            {"type": "recommendation", "value": {"field_label": "Overall, do you think we should select this applicant and their project to be part of the fellowship program?", "help_text": "", "info": None}, "id": "56264b32-fa39-4c08-b41e-68e9c54b2712"},
            {"type": "rich_text", "value": {"field_label": "If no, please select a reason why not.", "help_text": "", "required": "", "default_value": ""}, "id": "f0533950-57f5-4bb7-81ec-2d3813490c88"},
            {"type": "rich_text", "value": {"field_label": "Request specific questions", "help_text": "", "required": "", "default_value": ""}, "id": "ba789376-e3f9-434e-8da5-330811723b30"},
            {"type": "comments", "value": {"field_label": "Other comments", "help_text": "", "info": None}, "id": "e74e2581-d06c-43b1-9c0b-911407225834"}
        ]

        application_review_form, _ = ReviewForm.objects.get_or_create(name='Fellowship application review', defaults={'form_fields': json.dumps(data3)})

        return application_review_form

    def create_fellowship_proposal_review_form(self):

        data4 = [
            {"type": "recommendation", "value": {"field_label": "Overall, do you think we should select this applicant and their project to be part of the fellowship program?", "help_text": "", "info": None}, "id": "e1ea4f9d-64e2-4f28-a68a-851ec0f2d9ad"},
            {"type": "rich_text", "value": {"field_label": "If no, please select a reason why not.", "help_text": "", "required": "", "default_value": ""}, "id": "e68b6fe9-8b11-4cf0-8ae4-2ffed75e1e80"},
            {"type": "rich_text", "value": {"field_label": "If yes, but you believe some changes need to be made to the proposed effort, please let us know.", "help_text": "", "required": "", "default_value": ""}, "id": "a413f3a2-b486-4bf3-9e2d-c48d19626876"},
            {"type": "score", "value": {"field_label": "Goals and principles", "help_text": "", "required": ""}, "id": "d40e541c-ccc0-4ede-94d1-bd8680b47004"},
            {"type": "score", "value": {"field_label": "Technical merit", "help_text": "", "required": ""}, "id": "4af1e000-25be-4cf1-a787-8e5fd91feba8"},
            {"type": "score", "value": {"field_label": "Reasonable and realistic", "help_text": "", "required": ""}, "id": "f839ec7e-1136-4fcd-b59e-c04e02d5abf6"},
            {"type": "rich_text", "value": {"field_label": "Request specific questions", "help_text": "", "required": "", "default_value": ""}, "id": "536c963a-f183-45bc-b83f-458b46dc5542"},
            {"type": "comments", "value": {"field_label": "Anything else you'd like to give us feedback on?", "help_text": "", "info": None}, "id": "cc82ba7b-b55e-4309-85f0-f68ad6f43471"}
        ]

        proposal_review_form, _ = ReviewForm.objects.get_or_create(name='Fellowship proposal review', defaults={'form_fields': json.dumps(data4)})

        return proposal_review_form

    def create_fellowship_fund_type(self, application_form, proposal_form, application_review_form, proposal_review_form):
        try:
            fund = FundType.objects.get(title=FS_FUND_TITLE)
        except FundType.DoesNotExist:
            apply_home = ApplyHomePage.objects.first()

            fund = FundType(title=FS_FUND_TITLE, workflow_name='double')
            apply_home.add_child(instance=fund)

            fund_form = ApplicationBaseForm.objects.create(application=fund, form=application_form)
            fund_form2 = ApplicationBaseForm.objects.create(application=fund, form=proposal_form)
            fund.forms = [fund_form, fund_form2]
            fund_review_form = ApplicationBaseReviewForm.objects.create(application=fund, form=application_review_form)
            fund_review_form2 = ApplicationBaseReviewForm.objects.create(application=fund, form=proposal_review_form)
            fund.review_forms = [fund_review_form, fund_review_form2]
            fund.save()

        return fund

    def create_fellowship_round(self, fund):
        User = get_user_model()

        try:
            lead = User.objects.get(full_name="Lindsay Beck")
        except User.DoesNotExist:
            lead = User.objects.filter(groups__name=STAFF_GROUP_NAME).first()

        round = Round(
            title=FS_ROUND_TITLE,
            lead=lead,
            # The date of the original Information Controls Fellowship request type
            start_date=date(2015, 8, 28),
            end_date=None
        )
        round.parent_page = fund
        fund.add_child(instance=round)
