import json

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.categories.models import Category
from opentech.apply.funds.models import ApplicationForm, FundForm, FundType, Round
from opentech.apply.home.models import ApplyHomePage
from opentech.apply.users.groups import STAFF_GROUP_NAME


class Command(BaseCommand):
    help = "Pre-seeds the RR application form and fund type. Depends on the categories seed being run first."

    @transaction.atomic
    def handle(self, *args, **options):
        # There's an RR open round, so bail out. Avoids duplicate command runs.
        if Round.objects.filter(title='Rapid Response open round').count():
            return

        application_form = self.create_rapid_response_form()
        fund = self.create_rapid_response_fund_type(application_form)
        self.create_rapid_response_round(fund)

    def create_rapid_response_form(self):

        focus_id = Category.objects.get(name='Focus').id
        objectives_id = Category.objects.get(name='Objective(s)').id
        beneficiaries_id = Category.objects.get(name='Beneficiaries').id
        regions_id = Category.objects.get(name='Region(s)').id
        addressed_id = Category.objects.get(name='Addressed problems').id

        application_form, _ = ApplicationForm.objects.get_or_create(name='Rapid response', defaults={'form_fields': json.dumps([
            {"type": "text_markup", "value": "<h3>Basic information</h3>"},
            {"type": "title", "value": {"field_label": "What is your project name?", "help_text": "", "info": None}},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}},
            {"type": "dropdown", "value": {"field_label": "Have you ever applied to or received funding as an OTF project or fellow?", "help_text": "", "required": "true", "choices": ["Yes", "No"]}},
            {"type": "text_markup", "value": "<h3>More information about your project</h3>"},
            {"type": "radios", "value": {"field_label": "What are you applying for?", "help_text": "", "required": "true", "choices": ["Direct funding", "Requesting to receive services", "Requesting to provide services"]}},
            {"type": "value", "value": {"field_label": "If you are applying for direct funding, how much do you need?", "help_text": "Amount requested should be less than 50000 USD.", "info": None}},
            {"type": "dropdown", "value": {"field_label": "If you are requesting to receive or provide a service, what is it?", "help_text": "", "required": "false", "choices": ["Audit of presumably compromised websites", "DDoS response and mitigation", "Secure web hosting", "monitoring and resiliency of websites during special events (elections, campaigns etc.)", "VPN connections", "Safe internet connections", "Forensic analysis of digital attacks", "Recovery of compromised websites", "Malware analysis", "Equipment replacements", "Finding legal representation", "Payment of legal fees"]}},
            {"type": "rich_text", "value": {"field_label": "If not listed above, what other services do you want to provide or receive?", "help_text": "", "required": "false", "default_value": ""}},
            {"type": "dropdown", "value": {"field_label": "How long will it take?", "help_text": "", "required": "true", "choices": ["1 month", "2 months", "3 months", "4 months", "5 months", "6 months"]}},
            {"type": "rich_text", "value": {"field_label": "What is the challenge you are trying to address and who will it help?", "help_text": "Please briefly provide contextual or background information regarding the problem you would like to address and the target groups/communities you are trying to help.", "required": "true", "default_value": ""}},
            {"type": "rich_text", "value": {"field_label": "What are you proposing to do and how will you accomplish it?", "help_text": "In other words, please describe your project\\\\u2019s overall goal as well as specific objectives. What activities are you going to carry out in order to achieve your objectives?", "required": "true", "default_value": ""}},
            {"type": "rich_text", "value": {"field_label": "Anticipated outputs and outcomes", "help_text": "", "required": "true", "default_value": ""}},
            {"type": "rich_text", "value": {"field_label": "Timeline", "help_text": "", "required": "true", "default_value": ""}},
            {"type": "rich_text", "value": {"field_label": "How does this project fit into OTF’s Rapid Response remit?", "help_text": "", "required": "true", "default_value": ""}},
            {"type": "text_markup", "value": "<a href=\"\/requests\/rapid-response-fund\">Open the Rapid Response Fund remit in a new window.</a>"},
            {"type": "rich_text", "value": {"field_label": "Why does it have to happen immediately or within the next few months?", "help_text": "", "required": "true", "default_value": ""}},
            {"type": "category", "value": {"field_label": "Focus", "help_text": "", "required": "false", "category": focus_id, "multi": "true"}},
            {"type": "category", "value": {"field_label": "Objectives", "help_text": "", "required": "true", "category": objectives_id, "multi": "true"}},
            {"type": "category", "value": {"field_label": "Beneficiaries", "help_text": "", "required": "true", "category": beneficiaries_id, "multi": "true"}},
            {"type": "category", "value": {"field_label": "Regions", "help_text": "", "required": "true", "category": regions_id, "multi": "true"}},
            {"type": "category", "value": {"field_label": "Addressed problems", "help_text": "", "required": "true", "category": addressed_id, "multi": "true"}},
            {"type": "rich_text", "value": {"field_label": "Budget", "help_text": "", "required": "true", "default_value": ""}},
            {"type": "text_markup", "value": "<h3>Legal information for the contract</h3>"},
            {"type": "char", "value": {"field_label": "Legal name", "help_text": "", "required": "false", "format": "", "default_value": ""}},
            {"type": "char", "value": {"field_label": "Primary point of contact", "help_text": "", "required": "false", "format": "", "default_value": ""}},
            {"type": "char", "value": {"field_label": "Phone", "help_text": "", "required": "false", "format": "", "default_value": ""}},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": "false"}},
            {"type": "text_markup", "value": "<h3>I acknowledge</h3>"},
            {"type": "checkbox", "value": {"field_label": "My application will be dismissed if it does not fit within OTF\'s mission, values, principles statements.", "help_text": "", "default_value": "true"}},
            {"type": "text_markup", "value": "Read our <a href=\"\/about/program\">mission, values, and principles</a>."},
            {"type": "checkbox", "value": {"field_label": "I have read and understand OTF\'s Terms and Privacy policy.", "help_text": "", "default_value": "true"}},
            {"type": "text_markup", "value": "Read the <a href=\"\/tos\">Terms and Privacy policy</a>."},
            {"type": "checkbox", "value": {"field_label": "I am legally able to sign contracts or represent an organization that can.", "help_text": "", "default_value": "true"}},
            {"type": "checkbox", "value": {"field_label": "I understand that all intellectual property created with support for this application must be openly licensed.", "help_text": "", "default_value": "true"}},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is incomplete in any way, it will be dismissed.", "help_text": "", "default_value": "true"}},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is after a deadline, it will not be reviewed until after the next deadline.", "help_text": "", "default_value": "true"}},
            {"type": "text_markup", "value": "<h3>I would like to</h3>"},
            {"type": "checkbox", "value": {"field_label": "Sign up to the OTF-Announce list, low traffic (funding opportunities, major alerts, etc)", "help_text": "", "default_value": "false"}},
            {"type": "checkbox", "value": {"field_label": "Sign up for OTF\'s daily newsletter (collection of news related to global internet freedom).", "help_text": "", "default_value": "false"}}
        ])})

        return application_form

    def create_rapid_response_fund_type(self, application_form):
        try:
            fund = FundType.objects.get(title='Rapid Response')
        except FundType.DoesNotExist:
            apply_home = ApplyHomePage.objects.first()

            fund = FundType(title='Rapid Response', workflow_name='single')
            apply_home.add_child(instance=fund)

            fund_form = FundForm.objects.create(fund=fund, form=application_form)
            fund.forms = [fund_form]
            fund.save()

        return fund

    def create_rapid_response_round(self, fund):
        User = get_user_model()

        try:
            lead = User.objects.get(full_name="Lindsay Beck")
        except User.DoesNotExist:
            lead = User.objects.filter(groups__name=STAFF_GROUP_NAME).first()

        round = Round(
            title="Rapid Response open round",
            lead=lead,
            # The date of the original RR request type
            start_date=date(2015, 8, 28),
            end_date=None
        )
        fund.add_child(instance=round)
