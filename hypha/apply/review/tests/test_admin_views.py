import factory
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from hypha.apply.funds.tests.test_admin_views import create_form_fields_data
from hypha.apply.review.models import ReviewForm
from hypha.apply.users.tests.factories import SuperUserFactory


class TestCreateReviewFormView(TestCase):
    @classmethod
    def setUpTestData(cls):
        ReviewForm.objects.all().delete()
        cls.user = SuperUserFactory()
        cls.label_help_text_data = {
            "field_label": factory.Faker("sentence").evaluate(
                None, None, {"locale": None}
            ),
            "help_text": factory.Faker("sentence").evaluate(
                None, None, {"locale": None}
            ),
        }
        cls.name = factory.Faker("name").evaluate(None, None, {"locale": None})

    def create_page(self, data):
        self.client.force_login(self.user)
        url = reverse("review_reviewform_modeladmin_create")
        response = self.client.post(url, data=data, secure=True, follow=True)
        return response

    def test_name_field_required(self):
        data = {"name": [""]}
        form_field_data = create_form_fields_data(
            {
                "recommendation": self.label_help_text_data,
                "comments": self.label_help_text_data,
                "visibility": self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = "This field is required."
        for message in get_messages(response.context["request"]):
            self.assertEqual(expected_message, str(message.message).strip())
        self.assertEqual(ReviewForm.objects.count(), 0)

    def test_recommendation_block_required(self):
        data = {"name": [self.name]}
        form_field_data = create_form_fields_data(
            {
                "comments": self.label_help_text_data,
                "visibility": self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = (
            "You are missing the following required fields: Recommendation"
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(expected_message, str(messages[0]).strip())
        self.assertEqual(ReviewForm.objects.count(), 0)

    def test_comments_block_required(self):
        ReviewForm.objects.all().delete()
        data = {"name": [self.name]}
        form_field_data = create_form_fields_data(
            {
                "recommendation": self.label_help_text_data,
                "visibility": self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = "You are missing the following required fields: Comments"
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(expected_message, str(messages[0]).strip())
        self.assertEqual(ReviewForm.objects.count(), 0)

    def test_visibility_block_required(self):
        data = {"name": [self.name]}
        form_field_data = create_form_fields_data(
            {
                "recommendation": self.label_help_text_data,
                "comments": self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_message = "You are missing the following required fields: Visibility"
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(expected_message, str(messages[0]).strip())
        self.assertEqual(ReviewForm.objects.count(), 0)

    def test_field_label_required(self):
        data = {"name": [self.name]}
        form_field_data = create_form_fields_data(
            {
                "recommendation": {},
                "comments": {},
                "visibility": {},
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        expected_messages_list = [
            "Label cannot be empty for Recommendation",
            "Label cannot be empty for Comments",
            "Label cannot be empty for Visibility",
        ]
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 3)
        for message in messages:
            self.assertIn(str(message).strip(), expected_messages_list)
        self.assertEqual(ReviewForm.objects.count(), 0)

    def test_form_creation(self):
        data = {"name": [self.name]}
        form_field_data = create_form_fields_data(
            {
                "recommendation": self.label_help_text_data,
                "comments": self.label_help_text_data,
                "visibility": self.label_help_text_data,
            }
        )
        data.update(form_field_data)
        response = self.create_page(data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ReviewForm.objects.count(), 1)
