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

RR_ROUND_TITLE = 'Rapid Response open round'


class Command(BaseCommand):
    help = "Pre-seeds the RR application form and fund type. Depends on the categories seed being run first."

    @transaction.atomic
    def handle(self, *args, **options):
        # There's an RR open round, so bail out. Avoids duplicate command runs.
        if Round.objects.filter(title=RR_ROUND_TITLE).count():
            self.stdout.write(self.style.WARNING('Skipping. The target Round/Fund Type and Application Form exist'))
            return

        application_form = self.create_rapid_response_form()
        application_review_form = self.create_rapid_response_review_form()
        fund = self.create_rapid_response_fund_type(application_form, application_review_form)
        self.create_rapid_response_round(fund)

    def create_rapid_response_form(self):

        focus_id = Category.objects.get(name='Focus').id
        objectives_id = Category.objects.get(name='Objective(s)').id
        beneficiaries_id = Category.objects.get(name='Beneficiaries').id
        regions_id = Category.objects.get(name='Region(s)').id
        addressed_id = Category.objects.get(name='Addressed problems').id

        data = [
            {"type": "text_markup", "value": "<h3>Basic information</h3>", "id": "a96e8d83-edfc-42d2-a02a-c4f72cb94b84"},
            {"type": "title", "value": {"field_label": "What is your project name?", "help_text": "", "info": None}, "id": "09d320bc-9c20-4795-8823-54cab9cc6eaf"},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "a3580ace-11c4-4b79-bc5d-2445414782b7"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "14cda1f7-4553-43c6-9f09-944285246fbf"},
            {"type": "dropdown", "value": {"field_label": "Have you ever applied to or received funding as an OTF project or fellow?", "help_text": "", "required": "true", "choices": ["Yes", "No"]}, "id": "49a0f5f4-e8e9-4dfc-8575-205ee9675032"},
            {"type": "text_markup", "value": "<h3>More information about your project</h3>", "id": "37657bd3-04b0-4dbb-af2d-63065c349f82"},
            {"type": "radios", "value": {"field_label": "What are you applying for?", "help_text": "", "required": "true", "choices": ["Direct funding", "Requesting to receive services", "Requesting to provide services"]}, "id": "c1277029-1718-40e3-8bf5-d80ece7fd343"},
            {"type": "value", "value": {"field_label": "If you are applying for direct funding, how much do you need?", "help_text": "Amount requested should be less than 50000 USD.", "info": None}, "id": "cfae89dc-f327-45f4-80e9-f267c3bd1ec7"},
            {"type": "dropdown", "value": {"field_label": "If you are requesting to receive or provide a service, what is it?", "help_text": "", "required": "", "choices": ["Audit of presumably compromised websites", "DDoS response and mitigation", "Secure web hosting", "monitoring and resiliency of websites during special events (elections, campaigns etc.)", "VPN connections", "Safe internet connections", "Forensic analysis of digital attacks", "Recovery of compromised websites", "Malware analysis", "Equipment replacements", "Finding legal representation", "Payment of legal fees"]}, "id": "ebdf9a22-58c7-4bd6-a58d-e71363357470"},
            {"type": "rich_text", "value": {"field_label": "If not listed above, what other services do you want to provide or receive?", "help_text": "", "required": "", "default_value": ""}, "id": "c8c329c7-78e4-4cbf-a3b1-77a1324e92ff"},
            {"type": "duration", "value": {"field_label": "How long will it take?", "help_text": "", "info": None}, "id": "b47f84f5-81bc-4aff-a865-5b927f504246"},
            {"type": "rich_text", "value": {"field_label": "What is the challenge you are trying to address and who will it help?", "help_text": "Please briefly provide contextual or background information regarding the problem you would like to address and the target groups/communities you are trying to help.", "required": "true", "default_value": ""}, "id": "1ec16cdc-7a68-40be-b17b-9a218def4260"},
            {"type": "rich_text", "value": {"field_label": "What are you proposing to do and how will you accomplish it?", "help_text": "In other words, please describe your project\u2019s overall goal as well as specific objectives. What activities are you going to carry out in order to achieve your objectives?", "required": "true", "default_value": ""}, "id": "4fa2ac11-d1cd-4d23-8082-93a14c8f99c8"},
            {"type": "rich_text", "value": {"field_label": "Anticipated outputs and outcomes", "help_text": "", "required": "true", "default_value": ""}, "id": "3cde39ae-b687-4c4f-b58b-849396c2fdb8"},
            {"type": "rich_text", "value": {"field_label": "Timeline", "help_text": "", "required": "true", "default_value": ""}, "id": "0b2a4653-b390-44a6-b92e-fae4647e7ec4"},
            {"type": "rich_text", "value": {"field_label": "How does this project fit into OTF\u2019s Rapid Response remit?", "help_text": "", "required": "true", "default_value": ""}, "id": "6d75e412-cf53-4833-9f1d-3e0126512fb9"},
            {"type": "text_markup", "value": "<a href=\"\/requests\/rapid-response-fund\">Open the Rapid Response Fund remit in a new window.</a>", "id": "85d6c115-8d06-4a52-95cf-0e9096633bf0"},
            {"type": "rich_text", "value": {"field_label": "Why does it have to happen immediately or within the next few months?", "help_text": "", "required": "true", "default_value": ""}, "id": "1b181d1e-ef91-41af-b9c1-d096a991314b"},
            {"type": "category", "value": {"field_label": "Focus", "help_text": "", "required": "", "category": focus_id, "multi": "true"}, "id": "efd91eaf-378f-4aab-96cb-c5601155cbee"},
            {"type": "category", "value": {"field_label": "Objectives", "help_text": "", "required": "true", "category": objectives_id, "multi": "true"}, "id": "4be0c7bd-231d-4d9f-bd47-8589fc005f54"},
            {"type": "category", "value": {"field_label": "Beneficiaries", "help_text": "", "required": "true", "category": beneficiaries_id, "multi": "true"}, "id": "6e0293ee-218e-4c3b-b82d-5bf91fdb21c9"},
            {"type": "category", "value": {"field_label": "Regions", "help_text": "", "required": "true", "category": regions_id, "multi": "true"}, "id": "6ff029c6-c6d1-4c37-a49a-46181b1cd33d"},
            {"type": "category", "value": {"field_label": "Addressed problems", "help_text": "", "required": "true", "category": addressed_id, "multi": "true"}, "id": "7fb1001e-d458-414f-a5bb-006db6f89baf"},
            {"type": "rich_text", "value": {"field_label": "Budget", "help_text": "", "required": "true", "default_value": ""}, "id": "45d7d38a-9c9d-4c43-98df-bb95d4a1dd77"},
            {"type": "text_markup", "value": "<h3>Legal information for the contract</h3>", "id": "29432dd7-d5d8-42e7-8d54-3b45c576dd7d"},
            {"type": "char", "value": {"field_label": "Legal name", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "632065c5-860f-4751-9b31-52914d7c6448"},
            {"type": "char", "value": {"field_label": "Primary point of contact", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "13bb0d64-65f3-4340-8e7e-e5da80d706d5"},
            {"type": "char", "value": {"field_label": "Phone", "help_text": "", "required": "", "format": "", "default_value": ""}, "id": "2cb9fe4b-df45-4181-80e5-14382f853081"},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}, "id": "bd29eb88-9754-4305-9b2d-406a875ec56a"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "607daeba-1f33-4ad0-b135-eda743ba8e3a"},
            {"type": "text_markup", "value": "<h3>I acknowledge</h3>", "id": "5688ddc7-0397-41e7-9e6b-2c0fe44f42aa"},
            {"type": "checkbox", "value": {"field_label": "My application will be dismissed if it does not fit within OTF\'s mission, values, principles statements.", "help_text": "", "required": "true", "default_value": ""}, "id": "e695f0d7-4c74-4cc6-853f-bd62ecd19d3d"},
            {"type": "text_markup", "value": "Read our <a href=\"\/about/program\">mission, values, and principles</a>.", "id": "051be067-d45a-4bc3-8016-a09dadd734f5"},
            {"type": "checkbox", "value": {"field_label": "I have read and understand OTF\'s Terms and Privacy policy.", "help_text": "", "required": "true", "default_value": ""}, "id": "f40d1acc-d802-4cc6-b0e9-fff78dc54223"},
            {"type": "text_markup", "value": "Read the <a href=\"\/tos\">Terms and Privacy policy</a>.", "id": "bcf64886-df76-41d2-9a22-fb7e49a7718c"},
            {"type": "checkbox", "value": {"field_label": "I am legally able to sign contracts or represent an organization that can.", "help_text": "", "required": "true", "default_value": ""}, "id": "0b3c0827-38e2-439b-bca5-735835af1019"},
            {"type": "checkbox", "value": {"field_label": "I understand that all intellectual property created with support for this application must be openly licensed.", "help_text": "", "required": "true", "default_value": ""}, "id": "bc9c960e-a6f4-4bc2-b626-efb5bc5552c6"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is incomplete in any way, it will be dismissed.", "help_text": "", "required": "true", "default_value": ""}, "id": "5812b66d-630e-4ca2-8bea-819084278f55"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is after a deadline, it will not be reviewed until after the next deadline.", "help_text": "", "required": "true", "default_value": ""}, "id": "97d3746c-cf0f-449a-b3a3-7a9cdd45cc6d"},
            {"type": "text_markup", "value": "<h3>I would like to</h3>", "id": "e99c9dbe-f788-4eb2-813d-1787c0871210"},
            {"type": "checkbox", "value": {"field_label": "Sign up to the OTF-Announce list, low traffic (funding opportunities, major alerts, etc)", "help_text": "", "required": "true", "default_value": ""}, "id": "fc3d2a87-1151-418b-b1cd-9289f00bde35"},
            {"type": "checkbox", "value": {"field_label": "Sign up for OTF\'s daily newsletter (collection of news related to global internet freedom).", "help_text": "", "required": "true", "default_value": ""}, "id": "83ecc69a-f47c-495e-bc8f-326e55aed67a"}
        ]

        application_form, _ = ApplicationForm.objects.get_or_create(name='Rapid response', defaults={'form_fields': json.dumps(data)})

        return application_form

    def create_rapid_response_review_form(self):

        data2 = [
            {"type": "Recommendation", "value": {"field_label": "Do you think we should support this request?", "help_text": "", "info": None}, "id": "d350fbf9-e332-4d7f-b238-7f545cff927a"},
            {"type": "rich_text", "value": {"field_label": "Things that you liked", "help_text": "", "required": "", "default_value": ""}, "id": "cec815a0-fab1-4142-9fc6-71319b054b2a"},
            {"type": "rich_text", "value": {"field_label": "Things that concern you", "help_text": "", "required": "", "default_value": ""}, "id": "6915acf0-9a19-4e73-8d2b-d96e39e3b00e"},
            {"type": "score", "value": {"field_label": "How appropriate are the proposed objectives for rapid response support?", "help_text": "", "required": ""}, "id": "71bfe95d-89c5-401b-ae7a-778e91d5c8c5"},
            {"type": "score", "value": {"field_label": "How would you rate the applicant's capacity and knowledge to carry out this project?", "help_text": "", "required": ""}, "id": "3aa164c1-4386-4046-997a-a2778e1d894e"},
            {"type": "score", "value": {"field_label": "Does the applicant provide sufficient justification for the amount of funding requested (is this cost effective)?", "help_text": "", "required": ""}, "id": "7cc12bb6-4c12-48aa-a269-1fd6d725abfe"},
            {"type": "rich_text", "value": {"field_label": "Justification comments", "help_text": "", "required": "", "default_value": ""}, "id": "abc61bba-2a9e-4a9e-8c06-a1824ea2a998"},
            {"type": "Comments", "value": {"field_label": "Other comments", "help_text": "", "info": None}, "id": "d94e51d3-026c-443f-a98a-a66b1f6c968c"}
        ]

        rapid_response_review_form, _ = ReviewForm.objects.get_or_create(name='Rapid response review', defaults={'form_fields': json.dumps(data2)})

        return rapid_response_review_form

    def create_rapid_response_fund_type(self, application_form, application_review_form):
        try:
            fund = FundType.objects.get(title='Rapid Response')
        except FundType.DoesNotExist:
            apply_home = ApplyHomePage.objects.first()

            fund = FundType(title='Rapid Response', workflow_name='single')
            apply_home.add_child(instance=fund)

            fund_form = ApplicationBaseForm.objects.create(application=fund, form=application_form)
            fund.forms = [fund_form]
            fund_review_form = ApplicationBaseReviewForm.objects.create(application=fund, form=application_review_form)
            fund.review_forms = [fund_review_form]
            fund.save()

        return fund

    def create_rapid_response_round(self, fund):
        User = get_user_model()

        try:
            lead = User.objects.get(full_name="Lindsay Beck")
        except User.DoesNotExist:
            lead = User.objects.filter(groups__name=STAFF_GROUP_NAME).first()

        round = Round(
            title=RR_ROUND_TITLE,
            lead=lead,
            # The date of the original RR request type
            start_date=date(2015, 8, 28),
            end_date=None
        )
        round.parent_page = fund
        fund.add_child(instance=round)
