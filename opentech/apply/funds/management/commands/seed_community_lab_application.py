import json

from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.funds.models import ApplicationForm, LabForm, LabType
from opentech.apply.home.models import ApplyHomePage
from opentech.apply.users.groups import STAFF_GROUP_NAME


class Command(BaseCommand):
    help = "Pre-seeds the Community lab application form and lab type. Depends on the categories seed being run first."

    @transaction.atomic
    def handle(self, *args, **options):
        application_form = self.create_community_lab_form()
        self.create_community_lab_fund_type(application_form)

    def create_community_lab_form(self):

        data = [
            {"type": "text_markup", "value": "<h3>Basic information</h3>", "id": "33d38e10-43e3-4a61-8a10-2d3ad760861b"},
            {"type": "title", "value": {"field_label": "What is your project name?", "help_text": "", "info": None}, "id": "4507372e-a284-488a-ac3c-53b689849d67"},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "b62f1c35-52c7-44b5-b7cd-2f1aac6701bd"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "02a6cd0e-7ff6-46cd-9bdb-bf5858fe2514"},
            {"type": "date", "value": {"field_label": "Date of event", "help_text": "", "required": "", "default_value": ""}, "id": "8c74af9c-6cc7-4558-9d72-0f2c9a87f22b"},
            {"type": "value", "value": {"field_label": "Amount requested", "help_text": "", "info": None}, "id": "dfa76e03-0148-421b-a0fb-67f6fa1edee0"},
            {"type": "text_markup", "value": "<h3>More information about your product</h3>", "id": "d2090b37-11e0-4282-8f98-5edfb05918c0"},
            {"type": "rich_text", "value": {"field_label": "Please provide us a description of this event", "help_text": "", "required": "", "default_value": ""}, "id": "fe488e12-b5f4-491a-9ca9-d7aff0993884"},
            {"type": "rich_text", "value": {"field_label": "Please describe the target audience(s)", "help_text": "", "required": "", "default_value": ""}, "id": "e7a0bc56-ad5d-4be7-9709-eb823a0e6e3d"},
            {"type": "rich_text", "value": {"field_label": "What are the event’s objectives?", "help_text": "", "required": "", "default_value": ""}, "id": "43d52051-27f2-4d30-abf1-173a31f15072"},
            {"type": "rich_text", "value": {"field_label": "Please describe the strategy that will allow you to achieve your goals", "help_text": "", "required": "", "default_value": ""}, "id": "4e1f46ad-12d7-40c3-a1e8-0793bb327961"},
            {"type": "rich_text", "value": {"field_label": "How will this event support people living within a developing country affected by repressive censorship and/or surveillance?", "help_text": "", "required": "", "default_value": ""}, "id": "e33e1415-6832-4ef3-8a10-ae6d3aef61c8"},
            {"type": "rich_text", "value": {"field_label": "What collaborations with other organizations, communities, or networks exist around this event, if any?", "help_text": "", "required": "", "default_value": ""}, "id": "812792a3-edc5-4521-b5c7-e9c697122325"},
            {"type": "rich_text", "value": {"field_label": "How will the event ensure new and diverse voices are being represented?", "help_text": "", "required": "", "default_value": ""}, "id": "c367cae6-9fde-40fc-8c99-7ca2117bda6a"},
            {"type": "rich_text", "value": {"field_label": "Please describe the outreach and promotion plan for the event?", "help_text": "", "required": "", "default_value": ""}, "id": "14ef1b53-ef85-4756-a13e-19d3c3be7d85"},
            {"type": "rich_text", "value": {"field_label": "Is there anything you need help with in regards to planning this event that is non-monetary related?", "help_text": "For example, are there any audiences you are trying to cultivate? Do you need advice on the format of the event?", "required": "", "default_value": ""}, "id": "eb6474e1-2f69-4f69-9a9c-edf13c25455c"},
            {"type": "rich_text", "value": {"field_label": "Please provide a detailed budget", "help_text": "", "required": "", "default_value": ""}, "id": "de631da99f904f5f9c67e3a6e182f7c6"},
            {"type": "checkbox", "value": {"field_label": "Do you have a code of conduct?", "help_text": "If yes, upload it in the field below.", "required": "true", "default_value": "false"}, "id": "4948cc0fd1d142eeb81dd10784fba0f2"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "8c4f9cf13d624b64ab70e6cd342921f5"},
            {"type": "text_markup", "value": "<h3>I acknowledge</h3>", "id": "2c514f5844ae496085717dd48030d380"},
            {"type": "checkbox", "value": {"field_label": "My application will be dismissed if it does not fit within OTF\'s mission, values, principles statements.", "help_text": "", "required": "true", "default_value": ""}, "id": "9b20aa6384d54f64b1fb846efed89a41"},
            {"type": "text_markup", "value": "Read our <a href=\"\/about/program\">mission, values, and principles</a>.", "id": "cc52fb3e390647aa90024346af4dac3a"},
            {"type": "checkbox", "value": {"field_label": "I have read and understand OTF\'s Terms and Privacy policy.", "help_text": "", "required": "true", "default_value": ""}, "id": "b4a2f762f61c402aa8d22b58b3201263"},
            {"type": "text_markup", "value": "Read the <a href=\"\/tos\">Terms and Privacy policy</a>.", "id": "470782b4caf34cf89c9571eb16ae48cb"},
            {"type": "checkbox", "value": {"field_label": "I am legally able to sign contracts or represent an organization that can.", "help_text": "", "required": "true", "default_value": ""}, "id": "9409408f0cee4c97ac0517838eacdd9f"},
            {"type": "checkbox", "value": {"field_label": "I understand that all intellectual property created with support for this application must be openly licensed.", "help_text": "", "required": "true", "default_value": ""}, "id": "e0e6990db8744781afe9d42a105b8ff4"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is incomplete in any way, it will be dismissed.", "help_text": "", "required": "true", "default_value": ""}, "id": "966cd67f04a34c16b4e5892d4cd1e175"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is after a deadline, it will not be reviewed until after the next deadline.", "help_text": "", "required": "true", "default_value": ""}, "id": "d5b982f829dd4ee4aab3eb5349e6b077"},
            {"type": "text_markup", "value": "<h3>I would like to</h3>", "id": "2d813012ca1b44f6b42d560c1b475ff0"},
            {"type": "checkbox", "value": {"field_label": "Sign up to the OTF-Announce list, low traffic (funding opportunities, major alerts, etc)", "help_text": "", "required": "true", "default_value": ""}, "id": "4a4feb4e6e5445bd83b42e9f39ca833c"},
            {"type": "checkbox", "value": {"field_label": "Sign up for OTF\'s daily newsletter (collection of news related to global internet freedom).", "help_text": "", "required": "true", "default_value": ""}, "id": "e011bd48613648d48263997f71656bfc"}
        ]

        application_form, _ = ApplicationForm.objects.get_or_create(name='Community lab', defaults={'form_fields': json.dumps(data)})

        return application_form

    def create_community_lab_fund_type(self, application_form):
        User = get_user_model()

        try:
            lead = User.objects.get(full_name="Lindsay Beck")
        except User.DoesNotExist:
            lead = User.objects.filter(groups__name=STAFF_GROUP_NAME).first()

        try:
            lab = LabType.objects.get(title='Community lab')
        except LabType.DoesNotExist:
            apply_home = ApplyHomePage.objects.first()

            lab = LabType(title='Community lab', lead=lead, workflow_name='single')
            apply_home.add_child(instance=lab)

            lab_form = LabForm.objects.create(lab=lab, form=application_form)
            lab.forms = [lab_form]
            lab.save()

        return lab
