import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.funds.models import ApplicationForm, LabType
from opentech.apply.funds.models.forms import LabBaseForm, LabBaseReviewForm
from opentech.apply.review.models import ReviewForm

from opentech.apply.home.models import ApplyHomePage
from opentech.apply.users.groups import STAFF_GROUP_NAME

CL_FUND_TITLE = 'Community lab (archive fund)'


class Command(BaseCommand):
    help = "Pre-seeds the Community lab application form and lab type. Depends on the categories seed being run first."

    @transaction.atomic
    def handle(self, *args, **options):
        application_form = self.create_community_lab_form()
        application_review_form = self.create_community_lab_review_form()
        self.create_community_lab_fund_type(application_form, application_review_form)

    def create_community_lab_form(self):

        data = [
            {"type": "text_markup", "value": "<h3>Basic information</h3>", "id": "353df1fa-a054-406f-855f-842a52ad2852"},
            {"type": "title", "value": {"field_label": "What is your event name?", "help_text": "", "info": None}, "id": "690e7839-eedb-4c24-a438-91d09da88774"},
            {"type": "full_name", "value": {"field_label": "Your name", "help_text": "", "info": None}, "id": "4926d94b-7e57-494a-a2e2-2331a8ee04a2"},
            {"type": "email", "value": {"field_label": "E-mail", "help_text": "", "info": None}, "id": "f0b90755-dc11-4de7-89aa-7611bf698455"},
            {"type": "address", "value": {"field_label": "Address", "help_text": "", "info": None}, "id": "64a2f72a-9e3b-4b97-b69a-d0b9dbdd1cc7"},
            {"type": "date", "value": {"field_label": "Date of event", "help_text": "", "required": "", "default_value": ""}, "id": "d3364b5b-976b-4cd6-85d5-4ccc0bb9b560"},
            {"type": "value", "value": {"field_label": "Amount requested", "help_text": "", "info": None}, "id": "eadbd266-c825-45ea-8de9-deaa2aaa677b"},
            {"type": "duration", "value": {"field_label": "Duration", "help_text": "", "info": None}, "id": "9af05779-8547-4a85-8f1c-3505d5778e94"},
            {"type": "text_markup", "value": "<h3>More information about your product</h3>", "id": "17bc7cbe-49d7-42cf-8f60-1bbb0c841a1a"},
            {"type": "rich_text", "value": {"field_label": "Please provide us a description of this event", "help_text": "", "required": "", "default_value": ""}, "id": "aeea7bd9-01b5-406e-bb30-1303ba0f550a"},
            {"type": "rich_text", "value": {"field_label": "Please describe the target audience(s)", "help_text": "", "required": "", "default_value": ""}, "id": "a5117396-0286-4937-91a3-be33a5944ac6"},
            {"type": "rich_text", "value": {"field_label": "What are the event’s objectives?", "help_text": "", "required": "", "default_value": ""}, "id": "d90d2cd4-831e-46f5-8f2e-82ac94913784"},
            {"type": "rich_text", "value": {"field_label": "Please describe the strategy that will allow you to achieve your goals", "help_text": "", "required": "", "default_value": ""}, "id": "fc5ddac7-c7b5-4d07-9bc3-16902e9a7afb"},
            {"type": "rich_text", "value": {"field_label": "How will this event support people living within a developing country affected by repressive censorship and/or surveillance?", "help_text": "", "required": "", "default_value": ""}, "id": "ea6ceb76-882e-4739-94da-7b055a112d1c"},
            {"type": "rich_text", "value": {"field_label": "What collaborations with other organizations, communities, or networks exist around this event, if any?", "help_text": "", "required": "", "default_value": ""}, "id": "afa7e16b-d31c-4016-af88-7939acc7b6e1"},
            {"type": "rich_text", "value": {"field_label": "How will the event ensure new and diverse voices are being represented?", "help_text": "", "required": "", "default_value": ""}, "id": "55e23c45-72a7-4ab9-9940-764d00724de8"},
            {"type": "rich_text", "value": {"field_label": "Please describe the outreach and promotion plan for the event?", "help_text": "", "required": "", "default_value": ""}, "id": "737bd894-78b1-41ef-969c-2a57c843cd5b"},
            {"type": "rich_text", "value": {"field_label": "Is there anything you need help with in regards to planning this event that is non-monetary related?", "help_text": "For example, are there any audiences you are trying to cultivate? Do you need advice on the format of the event?", "required": "", "default_value": ""}, "id": "56c84f40-f59e-4e82-80a1-2cd971717e9c"},
            {"type": "rich_text", "value": {"field_label": "Please provide a detailed budget", "help_text": "", "required": "", "default_value": ""}, "id": "6ca29ae0-780a-467a-a3e9-34195bcb0d79"},
            {"type": "checkbox", "value": {"field_label": "Do you have a code of conduct?", "help_text": "If yes, upload it in the field below.", "required": "true", "default_value": "false"}, "id": "9db8b2ca-62b6-44c4-9d3d-70cb4a28e65f"},
            {"type": "multi_file", "value": {"field_label": "Upload", "help_text": "", "required": ""}, "id": "b3af7aac-3439-45fa-9573-518f82f5cd6c"},
            {"type": "text_markup", "value": "<h3>I acknowledge</h3>", "id": "b4bbe32a-058d-44b0-aaea-bddc70674277"},
            {"type": "checkbox", "value": {"field_label": "My application will be dismissed if it does not fit within OTF\'s mission, values, principles statements.", "help_text": "", "default_value": ""}, "id": "1248f597-2f18-4b16-8f96-63912e5197c5"},
            {"type": "text_markup", "value": "Read our <a href=\"\/about/program\">mission, values, and principles</a>.", "id": "67b65f65-5d9f-4152-9c0b-d980d9944e3d"},
            {"type": "checkbox", "value": {"field_label": "I have read and understand OTF\'s Terms and Privacy policy.", "help_text": "", "default_value": ""}, "id": "5a676552-e189-417e-9901-05bfc973cfb5"},
            {"type": "text_markup", "value": "Read the <a href=\"\/tos\">Terms and Privacy policy</a>.", "id": "f340a29d-56e3-4a01-be37-fc405cbafa8e"},
            {"type": "checkbox", "value": {"field_label": "I am legally able to sign contracts or represent an organization that can.", "help_text": "", "default_value": ""}, "id": "c4f54c3d-6b2a-4b32-b651-9121430aa06f"},
            {"type": "checkbox", "value": {"field_label": "I understand that all intellectual property created with support for this application must be openly licensed.", "help_text": "", "default_value": ""}, "id": "beb4d454-466d-43d5-823e-80dbccacbbb3"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is incomplete in any way, it will be dismissed.", "help_text": "", "default_value": ""}, "id": "fd6b034d-7cec-49fe-b4da-991c382283ef"},
            {"type": "checkbox", "value": {"field_label": "I understand that if my application is after a deadline, it will not be reviewed until after the next deadline.", "help_text": "", "default_value": ""}, "id": "d930a864-263d-4d0d-8ff1-553b13efda41"},
            {"type": "text_markup", "value": "<h3>I would like to</h3>", "id": "2b572f43-c912-4a94-93ae-cd6b64c2b95b"},
            {"type": "checkbox", "value": {"field_label": "Sign up to the OTF-Announce list, low traffic (funding opportunities, major alerts, etc).", "help_text": "", "default_value": ""}, "id": "f75fd335-be7d-460d-b96a-53d7aa9a826f"},
            {"type": "checkbox", "value": {"field_label": "Sign up for OTF\'s daily newsletter (collection of news related to global internet freedom).", "help_text": "", "default_value": ""}, "id": "a1f03bca-9267-49cf-9880-444d6806065c"}
        ]

        application_form, _ = ApplicationForm.objects.get_or_create(name='Community lab', defaults={'form_fields': json.dumps(data)})

        return application_form

    def create_community_lab_review_form(self):

        data2 = [
            {"type": "text_markup", "value": "<h3>Conflicts of Interest and Confidentialit</h3>", "id": "fe01dccb-87db-4dba-8cb8-f75e6f3448e6"},
            {"type": "checkbox", "value": {"field_label": "I understand about confidentiality", "help_text": "", "required": "true", "default_value": ""}, "id": "c1c6cedc-a084-4c55-87d5-7f6baf48441e"},
            {"type": "dropdown", "value": {"field_label": "Do you have any conflicts of interest to report?", "help_text": "", "required": "", "choices": ["Yes", "No"]}, "id": "c29a7f43-009c-4341-bbe8-9582ba089d52"},
            {"type": "rich_text", "value": {"field_label": "Conflict(s) of interest disclosure", "help_text": "", "required": "", "default_value": ""}, "id": "3aab69b1-6b60-4850-8f9f-7bc1b5871dcf"},
            {"type": "recommendation", "value": {"field_label": "Do you think we should support this request?", "help_text": "", "info": None}, "id": "caa6d522-4cfc-4f96-a29b-773a2de03e31"},
            {"type": "score", "value": {"field_label": "How well do the goals and objectives fit OTF’s remit?", "help_text": "", "required": ""}, "id": "732fc004-3086-44e1-8508-e0f17c3732a8"},
            {"type": "rich_text", "value": {"field_label": "What do you like about the proposed effort?", "help_text": "", "required": "", "default_value": ""}, "id": "f3c42cf1-e5ef-4674-bf6c-8e4640ee0d58"},
            {"type": "rich_text", "value": {"field_label": "What do you not like about the proposed effort?", "help_text": "", "required": "", "default_value": ""}, "id": "e1e69628-c663-4cd2-a0ea-507ad01149de"},
            {"type": "rich_text", "value": {"field_label": "What areas, if any, would you like more information?", "help_text": "", "required": "", "default_value": ""}, "id": "3033f228-58af-4944-b884-736fe6258bd6"},
            {"type": "rich_text", "value": {"field_label": "How could they can improve collaboration or the inclusion of diverse voices?", "help_text": "", "required": "", "default_value": ""}, "id": "20ec1ed7-4e3e-433c-944a-7c20cd6245c8"},
            {"type": "rich_text", "value": {"field_label": "Are there any individuals, communities, or networks they should reach out to?", "help_text": "", "required": "", "default_value": ""}, "id": "fd361c53-a263-4572-8403-74f6736d38fc"},
            {"type": "comments", "value": {"field_label": "Other comments", "help_text": "", "info": None}, "id": "d74e398e-6e64-43ae-b799-a3b79860c80e"}
        ]

        community_lab_review_form, _ = ReviewForm.objects.get_or_create(name='Community lab review', defaults={'form_fields': json.dumps(data2)})

        return community_lab_review_form

    def create_community_lab_fund_type(self, application_form, application_review_form):
        User = get_user_model()

        try:
            lead = User.objects.get(full_name="Lindsay Beck")
        except User.DoesNotExist:
            lead = User.objects.filter(groups__name=STAFF_GROUP_NAME).first()

        try:
            lab = LabType.objects.get(title=CL_FUND_TITLE)
        except LabType.DoesNotExist:
            apply_home = ApplyHomePage.objects.first()

            lab = LabType(title=CL_FUND_TITLE, lead=lead, workflow_name='single')
            apply_home.add_child(instance=lab)

            lab_form = LabBaseForm.objects.create(lab=lab, form=application_form)
            lab.forms = [lab_form]
            lab_review_form = LabBaseReviewForm.objects.create(lab=lab, form=application_review_form)
            lab.review_forms = [lab_review_form]
            lab.save()

        return lab
