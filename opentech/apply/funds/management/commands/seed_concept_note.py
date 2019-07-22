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

CN_ROUND_TITLE = 'Internet Freedom Fund (archive round)'
CN_FUND_TITLE = 'Internet Freedom Fund (archive fund)'


class Command(BaseCommand):
    help = "Pre-seeds the Concept notes form, proposal form and fund type. Depends on the categories seed being run first."

    @transaction.atomic
    def handle(self, *args, **options):
        # There's an Internet Freedom Fund open round, so bail out. Avoids duplicate command runs.
        if Round.objects.filter(title=CN_ROUND_TITLE).count():
            self.stdout.write(self.style.WARNING('Skipping. The target Round/Fund Type and Application Form exist'))
            return

        application_form = self.create_concept_note_form()
        proposal_form = self.create_proposal_form()
        application_review_form = self.create_concept_review_form()
        proposal_review_form = self.create_proposal_review_form()
        fund = self.create_concept_note_fund_type(application_form, proposal_form, application_review_form, proposal_review_form)
        self.create_concept_note_round(fund)

    def create_concept_note_form(self):

        focus_id = Category.objects.get(name='Focus').id
        objectives_id = Category.objects.get(name='Objective(s)').id
        beneficiaries_id = Category.objects.get(name='Beneficiaries').id
        regions_id = Category.objects.get(name='Region(s)').id
        addressed_id = Category.objects.get(name='Addressed problems').id
        status_id = Category.objects.get(name='Project status').id
        tech_id = Category.objects.get(name='Technology attributes').id
        countries_id = Category.objects.get(name='Countries').id

        data = [
            {"type": "text_markup", "value": "<h3>Basic information</h3>", "id": "25108c8b-c268-4f47-a441-99c3bc4ce43a"},
            {"type": "title", "value": {"field_label": "What is your project name?", "help_text": "", "info": None}, "id": "fd8e6437-89a4-4515-84d0-15c31be716ea"},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "825f74bf-9419-411a-97d1-631346ae7218"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "d66e3f38-48db-498a-83a5-4781ded03941"},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}, "id": "ea070127-684c-4136-8489-63c352b409c9"},
            {"type": "dropdown", "value": {"field_label": "Have you ever applied to or received funding as an OTF project?", "help_text": "", "required": "", "choices": ["Yes", "No"]}, "id": "0305a465-8763-4c1f-9197-4ca4227d452a"},
            {"type": "rich_text", "value": {"field_label": "If yes, which application and what was the outcome?", "help_text": "", "required": "", "default_value": ""}, "id": "c24691be-9861-4dbc-8be4-03b6e68c1973"},
            {"type": "text_markup", "value": "<h3>What is your idea?</h3>", "id": "0702b9e5-2624-40a0-9caa-42ff46797fb6"},
            {"type": "rich_text", "value": {"field_label": "Describe it", "help_text": "", "required": "", "default_value": ""}, "id": "c21c58c3-cfbe-4409-b2f2-8f56398f1731"},
            {"type": "rich_text", "value": {"field_label": "What are hoped for goals or longer term effects of the project?", "help_text": "", "required": "", "default_value": ""}, "id": "27289c14-6926-4f61-bea2-8031a653f71c"},
            {"type": "category", "value": {"field_label": "Focus", "help_text": "", "required": "", "category": focus_id, "multi": "true"}, "id": "404e2310-000b-4ccb-b772-3680946ff07d"},
            {"type": "category", "value": {"field_label": "Status", "help_text": "", "required": "", "category": status_id, "multi": "true"}, "id": "145c364f-e0bb-4652-94e8-fe08c831da2b"},
            {"type": "category", "value": {"field_label": "Technology attributes", "help_text": "", "required": "", "category": tech_id, "multi": "true"}, "id": "b4da2310-9654-4aa7-a04a-06335967ddc5"},
            {"type": "text_markup", "value": "<h3>How will you do it?</h3>", "id": "e5fe71f5-8ec5-4ac9-ba21-38e03cdcf73b"},
            {"type": "rich_text", "value": {"field_label": "Describe how", "help_text": "", "required": "", "default_value": ""}, "id": "418b8099-4525-437f-a55c-9b35745d0384"},
            {"type": "category", "value": {"field_label": "Objective(s)", "help_text": "", "required": "", "category": objectives_id, "multi": "true"}, "id": "390702bd-e4e1-4dc2-8c43-d51bf018b427"},
            {"type": "duration", "value": {"field_label": "How long will it take?", "help_text": "", "info": None}, "id": "b8d4f24f-c5bd-4a18-aa13-7c7358b3f99f"},
            {"type": "value", "value": {"field_label": "How much do you want?", "help_text": "", "info": None}, "id": "1e669b4d-e43f-4c7a-9730-08e25cb1592d"},
            {"type": "rich_text", "value": {"field_label": "How long have you been thinking of working on this idea? What made you first think about it?", "help_text": "", "required": "", "default_value": ""}, "id": "dfb9c307-9328-4a99-9efc-321d474b2ba7"},
            {"type": "text_markup", "value": "<h3>Who is the project for?</h3>", "id": "563c12f1-d856-4ee2-a449-793bbfd12296"},
            {"type": "rich_text", "value": {"field_label": "Describe them", "help_text": "", "required": "", "default_value": ""}, "id": "11f94a22-0571-4491-a93e-87c050e02a4a"},
            {"type": "rich_text", "value": {"field_label": "What community currently exists around this project?", "help_text": "", "required": "", "default_value": ""}, "id": "c272969b-d89f-4b6e-859f-4606a15b3f28"},
            {"type": "category", "value": {"field_label": "Beneficiaries", "help_text": "", "required": "", "category": beneficiaries_id, "multi": "true"}, "id": "72002c3e-aaee-47da-9377-8bb493f14c21"},
            {"type": "category", "value": {"field_label": "Region", "help_text": "", "required": "", "category": regions_id, "multi": "true"}, "id": "369b248e-f669-4aeb-b771-7cba0eadb921"},
            {"type": "category", "value": {"field_label": "Country", "help_text": "", "required": "", "category": countries_id, "multi": "true"}, "id": "57bceb33-ebda-4708-9080-fd1a5923e008"},
            {"type": "text_markup", "value": "<h3>Why is this project needed?</h3>", "id": "ab556178-07b5-468e-b1cf-46655859fd32"},
            {"type": "rich_text", "value": {"field_label": "Describe why", "help_text": "", "required": "", "default_value": ""}, "id": "c14ee077-c0eb-48b1-9825-fbba9b91ede5"},
            {"type": "category", "value": {"field_label": "Addressed problems", "help_text": "", "required": "", "category": addressed_id, "multi": "true"}, "id": "a83a1884-f711-4196-8d15-ae2110466acb"},
            {"type": "rich_text", "value": {"field_label": "Similar/Complementary efforts", "help_text": "", "required": "", "default_value": ""}, "id": "9ca35708-d611-4cd0-8d4a-3cc08349f45b"},
            {"type": "rich_text", "value": {"field_label": "Other information", "help_text": "", "required": "", "default_value": ""}, "id": "db7b1642-c03d-4af4-82c9-db67bf9713b0"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "8a91231c-5c3d-46fe-9de6-8d5c86817626"},
            {"type": "text_markup", "value": "<h3>I acknowledge</h3>", "id": "2c1651a4-2cdc-4b74-8b6e-f077364ca4d8"},
            {"type": "checkbox", "value": {"field_label": "My application will be dismissed if it does not fit within OTF\'s mission, values, principles statements.", "help_text": "", "default_value": ""}, "id": "4c661a64-2614-4169-b4d2-1fd39e2e831b"},
            {"type": "text_markup", "value": "Read our <a href=\"\/about/program\">mission, values, and principles</a>.", "id": "cfdd721d-a4d6-44a8-a2d6-6576f126799b"},
            {"type": "checkbox", "value": {"field_label": "I have read and understand OTF\'s Terms and Privacy policy.", "help_text": "", "default_value": ""}, "id": "1bc4e113-1414-46ff-bba7-2dc02b2126df"},
            {"type": "text_markup", "value": "Read the <a href=\"\/tos\">Terms and Privacy policy</a>.", "id": "d1c79c07-02cb-4f59-b5ed-719da7bdd636"},
            {"type": "checkbox", "value": {"field_label": "I am legally able to sign contracts or represent an organization that can.", "help_text": "", "default_value": ""}, "id": "42dd68a1-b699-4678-bea6-13e0f842e821"},
            {"type": "checkbox", "value": {"field_label": "I understand that all intellectual property created with support for this application must be openly licensed.", "help_text": "", "default_value": ""}, "id": "72916731-ec97-4688-95f1-d3bf140b03c2"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is incomplete in any way, it will be dismissed.", "help_text": "", "default_value": ""}, "id": "6856d26d-b169-4fdf-b598-63c3dd9278a2"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is after a deadline, it will not be reviewed until after the next deadline.", "help_text": "", "default_value": ""}, "id": "33838399-f292-4b63-83f0-e02d344f99d4"},
            {"type": "text_markup", "value": "<h3>I would like to</h3>", "id": "3ff08317-92ab-4eb1-adca-08547bed96f8"},
            {"type": "checkbox", "value": {"field_label": "Sign up to the OTF-Announce list, low traffic (funding opportunities, major alerts, etc).", "help_text": "", "default_value": ""}, "id": "fc571e12-d4a2-4d53-ab34-2c57321dc6ac"},
            {"type": "checkbox", "value": {"field_label": "Sign up for OTF\'s daily newsletter (collection of news related to global internet freedom).", "help_text": "", "default_value": ""}, "id": "cd0d8a4b-e71a-4dff-964a-f547bd655e7d"}
        ]

        application_form, _ = ApplicationForm.objects.get_or_create(name='Concept note', defaults={'form_fields': json.dumps(data)})

        return application_form

    def create_proposal_form(self):

        focus_id = Category.objects.get(name='Focus').id
        objectives_id = Category.objects.get(name='Objective(s)').id
        beneficiaries_id = Category.objects.get(name='Beneficiaries').id
        regions_id = Category.objects.get(name='Region(s)').id
        addressed_id = Category.objects.get(name='Addressed problems').id
        status_id = Category.objects.get(name='Project status').id
        tech_id = Category.objects.get(name='Technology attributes').id
        countries_id = Category.objects.get(name='Countries').id

        data2 = [
            {"type": "text_markup", "value": "<h3>Proposal information</h3>", "id": "f6bdb7e0-ec19-4b88-a2df-f0e7a512df8d"},
            {"type": "title", "value": {"field_label": "Proposal title", "help_text": "", "info": None}, "id": "6a83b04d-0909-4018-bc77-f8d72a019dd4"},
            {"type": "value", "value": {"field_label": "Requested funding", "help_text": "", "info": None}, "id": "0299f96f-3809-4f9e-a786-4af89547881b"},
            {"type": "duration", "value": {"field_label": "How long will it take?", "help_text": "", "info": None}, "id": "3ff602a1-642b-4742-a2c9-c9226af727ac"},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "739a413b-46cc-4936-82ce-e68c2dfa41ca"},
            {"type": "char", "value": {"field_label": "Legal name", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "d5cd3d89-89ea-44c2-9772-0da658c36881"},
            {"type": "char", "value": {"field_label": "Primary point of contact", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "a3c9af86-d047-4663-864a-b6dd97a60c39"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "6c95d411-bd68-4374-8c2d-1b64dc03ed68"},
            {"type": "char", "value": {"field_label": "Phone", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "40479d2a-7d53-4c81-834a-775ccd6c91c0"},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}, "id": "f7e431b1-9965-4ebe-ab30-a00ff4b972ec"},
            {"type": "text_markup", "value": "<h3>Proposal narrative</h3>", "id": "07f2ffb3-4eda-4f4c-8ebc-9da157e0102c"},
            {"type": "rich_text", "value": {"field_label": "Summary", "help_text": "", "required": "", "default_value": ""}, "id": "a7502e97-5f2e-417f-b08c-588d367e40e5"},
            {"type": "rich_text", "value": {"field_label": "Project description", "help_text": "", "required": "", "default_value": ""}, "id": "072f181b-90a2-4bb2-986d-55e1aaa9f348"},
            {"type": "rich_text", "value": {"field_label": "Objectives", "help_text": "", "required": "", "default_value": ""}, "id": "a7ae7375-4569-47e2-8ee7-3c3d441375a9"},
            {"type": "rich_text", "value": {"field_label": "Project deliverables/activities", "help_text": "", "required": "", "default_value": ""}, "id": "50328cc9-879d-4817-8454-2062ac47aef9"},
            {"type": "rich_text", "value": {"field_label": "Budget details", "help_text": "", "required": "", "default_value": ""}, "id": "7b0b0af4-009f-45db-b20c-5f991bce7752"},
            {"type": "rich_text", "value": {"field_label": "Similar/Complementary efforts", "help_text": "", "required": "", "default_value": ""}, "id": "ba3733f3-bee8-4fe8-bdde-36812aa4df77"},
            {"type": "rich_text", "value": {"field_label": "Monitoring and evaluation", "help_text": "", "required": "", "default_value": ""}, "id": "23028eab-92c3-4c30-9a3e-5604dec0854d"},
            {"type": "rich_text", "value": {"field_label": "Sustainability", "help_text": "", "required": "", "default_value": ""}, "id": "88d635e4-81d6-413c-8e09-52b74015e78b"},
            {"type": "rich_text", "value": {"field_label": "Other support information", "help_text": "", "required": "", "default_value": ""}, "id": "38072bb7-fcdd-4f74-9bfb-db45bfeb07a7"},
            {"type": "rich_text", "value": {"field_label": "Organization/Individual background", "help_text": "", "required": "", "default_value": ""}, "id": "f8b340d0-8c0c-41f8-acb5-662c676e2bbd"},
            {"type": "rich_text", "value": {"field_label": "References", "help_text": "", "required": "", "default_value": ""}, "id": "8b2572ce-d118-41c4-b5d7-59f4ffe44431"},
            {"type": "rich_text", "value": {"field_label": "Community interaction", "help_text": "", "required": "", "default_value": ""}, "id": "1b93fcd1-c6cd-432a-b831-a0fb680e327e"},
            {"type": "text_markup", "value": "<h3>Descriptors</h3>", "id": "a337e150-d3c5-40b0-9e9e-033c3a685290"},
            {"type": "category", "value": {"field_label": "Status", "help_text": "", "required": "", "category": status_id, "multi": "true"}, "id": "036fa233-c42a-4fc6-861a-ff40450efc7d"},
            {"type": "category", "value": {"field_label": "Focus", "help_text": "", "required": "", "category": focus_id, "multi": "true"}, "id": "7d69aeec-009d-4de2-8dd2-6b0aacb4578f"},
            {"type": "category", "value": {"field_label": "Objective(s)", "help_text": "", "required": "", "category": objectives_id, "multi": "true"}, "id": "328590d3-fefd-410d-b745-12f2efdd5437"},
            {"type": "category", "value": {"field_label": "Beneficiaries", "help_text": "", "required": "", "category": beneficiaries_id, "multi": "true"}, "id": "f18f0399-538b-4bf3-9cd5-4457138814a8"},
            {"type": "category", "value": {"field_label": "Addressed problems", "help_text": "", "required": "", "category": addressed_id, "multi": "true"}, "id": "a9b2b6de-fb7b-4709-aa59-f0ad987a677a"},
            {"type": "category", "value": {"field_label": "Technology attributes", "help_text": "", "required": "", "category": tech_id, "multi": "true"}, "id": "251cf41a-0a49-4725-8d5a-5e496d018647"},
            {"type": "category", "value": {"field_label": "Region", "help_text": "", "required": "", "category": regions_id, "multi": "true"}, "id": "ed6244ae-6903-4412-8b7a-c219ed25dfbb"},
            {"type": "category", "value": {"field_label": "Country", "help_text": "", "required": "", "category": countries_id, "multi": "true"}, "id": "4b79c527-bf24-47f1-87a7-39945e70caeb"},
            {"type": "text_markup", "value": "<h3>Other</h3>", "id": "3cb5d831-bb5d-494a-946a-b24f7867027c"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "6bec61a1-3527-4e21-aa65-f26d845bbb68"},
            {"type": "rich_text", "value": {"field_label": "Comments", "help_text": "", "required": "", "default_value": ""}, "id": "c0ff8444-8d43-46ef-8498-ed1a32c09c6a"}
        ]

        proposal_form, _ = ApplicationForm.objects.get_or_create(name='Proposal', defaults={'form_fields': json.dumps(data2)})

        return proposal_form

    def create_concept_review_form(self):

        data3 = [
            {"type": "recommendation", "value": {"field_label": "Do you think we should support this request?", "help_text": "", "info": None}, "id": "25d0d9b0-6e65-4fe3-906a-a1cd211def96"},
            {"type": "rich_text", "value": {"field_label": "Recommendation comments", "help_text": "", "required": "", "default_value": ""}, "id": "f16be0b3-ef02-4876-b056-8a84238b1a52"},
            {"type": "score", "value": {"field_label": "Goals and principles", "help_text": "", "required": ""}, "id": "6dd8d5d2-09a5-4681-aebc-eb9ccd00395a"},
            {"type": "score", "value": {"field_label": "Technical merit", "help_text": "", "required": ""}, "id": "52b1f53c-9656-4b0c-8b8b-a9c57869356d"},
            {"type": "score", "value": {"field_label": "Reasonable and realistic", "help_text": "", "required": ""}, "id": "aedb27e7-6044-4e04-b2c7-358065c8fe5c"},
            {"type": "rich_text", "value": {"field_label": "Request specific questions", "help_text": "", "required": "", "default_value": ""}, "id": "84405ba2-f94e-4d4d-92e1-190bd802f858"},
            {"type": "comments", "value": {"field_label": "Other comments", "help_text": "", "info": None}, "id": "5028cac1-752f-4d47-b83a-4f766f19fb2d"}
        ]

        concept_review_form, _ = ReviewForm.objects.get_or_create(name='Concept review', defaults={'form_fields': json.dumps(data3)})

        return concept_review_form

    def create_proposal_review_form(self):

        data4 = [
            {"type": "text_markup", "value": "<h3>A. Conflicts of Interest and Confidentialit</h3>", "id": "976386e1-3a66-490f-9e82-bfbe1f134cf2"},
            {"type": "checkbox", "value": {"field_label": "I understand about confidentiality", "help_text": "", "default_value": ""}, "id": "65fb2c22-a0c5-4cde-94a7-feb27072bc3d"},
            {"type": "dropdown", "value": {"field_label": "Do you have any conflicts of interest to report?", "help_text": "", "required": "", "choices": ["Yes", "No"]}, "id": "dd75ce49-e3c4-43da-b724-4cb8bb88dcf8"},
            {"type": "rich_text", "value": {"field_label": "Conflict(s) of interest disclosure", "help_text": "", "required": "", "default_value": ""}, "id": "9f7fe70b-97b5-4263-98ac-a45bf97b59d0"},
            {"type": "text_markup", "value": "<h3>B. General thoughts</h3>", "id": "976386e1-3a66-490f-9e82-bfbe1f134cf2"},
            {"type": "rich_text", "value": {"field_label": "1. Positive aspects", "help_text": "", "required": "", "default_value": ""}, "id": "e91ed603-61ad-483e-be7b-21716d05a3bd"},
            {"type": "rich_text", "value": {"field_label": "2. Concerns", "help_text": "", "required": "", "default_value": ""}, "id": "821fb071-7db7-4cc1-ac3a-34b9eee40c94"},
            {"type": "rich_text", "value": {"field_label": "3. Items that must be addressed", "help_text": "", "required": "", "default_value": ""}, "id": "021624ac-6628-430d-ba86-e68fd518c87e"},
            {"type": "text_markup", "value": "<h3>C. Specific aspects</h3>", "id": "976386e1-3a66-490f-9e82-bfbe1f134cf2"},
            {"type": "score", "value": {"field_label": "1. Project overview", "help_text": "", "required": ""}, "id": "9c5603d5-f897-42fa-8739-5935769c94bd"},
            {"type": "score", "value": {"field_label": "2. Proposal objectives", "help_text": "", "required": ""}, "id": "6b748400-fad9-4b31-bb85-e3a53c99f4df"},
            {"type": "score", "value": {"field_label": "3. Appropriate activities and strategy", "help_text": "", "required": ""}, "id": "a806a944-1d8a-4904-ace0-acfce5634a50"},
            {"type": "score", "value": {"field_label": "4. Technical feasibility (where applicable)", "help_text": "", "required": ""}, "id": "512a86a5-ec5b-4d36-9630-90648b5b43e4"},
            {"type": "score", "value": {"field_label": "5. Alternative analysis - red teaming", "help_text": "", "required": ""}, "id": "d9695d1d-3373-4acf-ada5-3b2593b3a634"},
            {"type": "score", "value": {"field_label": "6. Usability", "help_text": "", "required": ""}, "id": "e43dd4dc-d2fa-493c-9f55-5a126d0e0579"},
            {"type": "score", "value": {"field_label": "7. Sustainability", "help_text": "", "required": ""}, "id": "ee7009b8-ad18-46b5-a981-ccc52972c0a5"},
            {"type": "score", "value": {"field_label": "8. Collaboration", "help_text": "", "required": ""}, "id": "dc5dc5e0-e4d6-462f-8296-a0e58933e701"},
            {"type": "score", "value": {"field_label": "9. Cost realism", "help_text": "", "required": ""}, "id": "31e9b202-24b1-4993-80b7-9851624e2162"},
            {"type": "score", "value": {"field_label": "10. Qualifications", "help_text": "", "required": ""}, "id": "d3f5479c-68da-41d9-a266-130d383bab6b"},
            {"type": "score", "value": {"field_label": "11. Evaluation", "help_text": "", "required": ""}, "id": "2a61c71a-74f6-4963-8850-9289e852f604"},
            {"type": "text_markup", "value": "<h3>D. Rationale and appropriateness consideration</h3>", "id": "976386e1-3a66-490f-9e82-bfbe1f134cf2"},
            {"type": "score", "value": {"field_label": "Rationale and appropriateness", "help_text": "", "required": ""}, "id": "0d1bf533-968c-44b9-bb30-d437ae039474"},
            {"type": "text_markup", "value": "<h3>E. General recommendation</h3>", "id": "976386e1-3a66-490f-9e82-bfbe1f134cf2"},
            {"type": "recommendation", "value": {"field_label": "Recommendation", "help_text": "", "info": None}, "id": "4bf80578-1c8f-4515-9d6a-e52e87629e3e"},
            {"type": "comments", "value": {"field_label": "Recommendation comments", "help_text": "", "info": None}, "id": "a814d7ac-8291-4f3e-b733-4a9a4f1f8a49"}
        ]

        proposal_review_form, _ = ReviewForm.objects.get_or_create(name='Proposal review', defaults={'form_fields': json.dumps(data4)})

        return proposal_review_form

    def create_concept_note_fund_type(self, application_form, proposal_form, application_review_form, proposal_review_form):
        try:
            fund = FundType.objects.get(title=CN_FUND_TITLE)
        except FundType.DoesNotExist:
            apply_home = ApplyHomePage.objects.first()

            fund = FundType(title=CN_FUND_TITLE, workflow_name='double')
            apply_home.add_child(instance=fund)

            fund_form = ApplicationBaseForm.objects.create(application=fund, form=application_form)
            fund_form2 = ApplicationBaseForm.objects.create(application=fund, form=proposal_form)
            fund.forms = [fund_form, fund_form2]
            fund_review_form = ApplicationBaseReviewForm.objects.create(application=fund, form=application_review_form)
            fund_review_form2 = ApplicationBaseReviewForm.objects.create(application=fund, form=proposal_review_form)
            fund.review_forms = [fund_review_form, fund_review_form2]
            fund.save()

        return fund

    def create_concept_note_round(self, fund):
        User = get_user_model()

        try:
            lead = User.objects.get(full_name="Lindsay Beck")
        except User.DoesNotExist:
            lead = User.objects.filter(groups__name=STAFF_GROUP_NAME).first()

        round = Round(
            title=CN_ROUND_TITLE,
            lead=lead,
            # The date of the original Internet Freedom Fund request type
            start_date=date(2013, 1, 1),
            end_date=date(2018, 8, 29)
        )
        round.parent_page = fund
        fund.add_child(instance=round)
