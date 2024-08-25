import json
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from faker import Faker

from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.funds.blocks import (
    AddressFieldBlock,
    DurationBlock,
    EmailBlock,
    FullNameBlock,
    TitleBlock,
    ValueBlock,
)
from hypha.apply.funds.models import (
    ApplicationRevision,
    ApplicationSubmission,
)
from hypha.apply.review.blocks import (
    RecommendationBlock,
    RecommendationCommentsBlock,
    ScoreFieldBlock,
    ScoreFieldWithoutTextBlock,
    VisibilityBlock,
)
from hypha.apply.review.models import (
    Review,
)
from hypha.apply.review.options import (
    RATE_CHOICES,
    RECOMMENDATION_CHOICES,
)
from hypha.apply.stream_forms.blocks import (
    CharFieldBlock,
    CheckboxFieldBlock,
    DropdownFieldBlock,
    MultiFileFieldBlock,
    RadioButtonsFieldBlock,
    TextFieldBlock,
)
from hypha.apply.utils.blocks import RichTextFieldBlock, SingleIncludeMixin


class Command(BaseCommand):
    help = "Sanitizes the reviews, submissions, and users of identifiable inforamtion"

    def add_arguments(self, parser):
        parser.add_argument(
            "--exclude",
            action="append",
            help="Exclude user identified by email address from sanitization",
        )

    def sanitize(self, form_holder):
        for form_field in form_holder.form_fields:
            data = None
            key = None
            if isinstance(form_field.block, SingleIncludeMixin):
                try:
                    data = form_holder.form_data[form_field.block_type]
                    key = form_field.block_type
                except:  # noqa: E722
                    pass
            if not data and form_field.id in form_holder.form_data:
                data = form_holder.form_data[form_field.id]
                key = form_field.id

            if data is None:
                continue

            def update_data(new_data):
                if not data:  # noqa: B023
                    # Don't replace non data with data!!
                    pass
                else:
                    form_holder.form_data[key] = new_data  # noqa: B023

            def update_text_data():
                if len(data) == 5:  # noqa: B023
                    # Don't replace empty strings with non empty strings
                    pass
                elif len(data) < 5:  # noqa: B023
                    update_data(self.f.word())
                else:
                    update_data(self.f.text(len(data)))  # noqa: B023

            if form_field.value["field_label"].lower() == "organization name":
                update_data(self.f.company())
            elif form_field.value["field_label"].lower() == "contact phone number":
                update_data(self.f.phone_number())
            elif (
                form_field.value["field_label"].lower() == "organization address"
                or type(form_field.block) is AddressFieldBlock
            ):
                try:
                    address = json.loads(data)
                    address["country"] = self.f.country_code()
                    address["thoroughfare"] = self.f.street_address()
                    address["premise"] = ""
                    address["localityname"] = self.f.city()
                    address["administrativearea"] = "CA"
                    address["postalcode"] = self.f.postcode()
                    update_data(json.dumps(address))
                except json.decoder.JSONDecodeError:
                    # Address was just a string
                    update_data(self.f.address())
            elif form_field.value["field_label"].lower() == "requested grant amount":
                update_data(self.f.pricetag())
            elif form_field.value["field_label"].lower() == "project website":
                update_data(self.f.uri())
            elif (
                form_field.value["field_label"].lower()
                == "requested grant amount currency (if not us dollars)"
            ):
                update_data(self.f.currency_code())
            elif form_field.value["field_label"].lower() == "additional contact name":
                update_data(self.f.name())
            elif (
                form_field.value["field_label"].lower()
                == "ein (for us-based organizations)"
            ):
                update_data(self.f.ssn())
            elif form_field.value["field_label"].lower() == "additional contact email":
                update_data(self.f.email())
            elif type(form_field.block) is FullNameBlock:
                update_data(self.f.name())
            elif type(form_field.block) is EmailBlock:
                update_data(self.f.email())
            elif type(form_field.block) is TitleBlock:
                update_data(self.f.sentence(5))
            elif type(form_field.block) is MultiFileFieldBlock:
                update_data([])
            elif type(form_field.block) is RecommendationBlock:
                update_data(random.choice(RECOMMENDATION_CHOICES)[0])
            elif type(form_field.block) is ScoreFieldBlock:
                update_data(random.choice(RATE_CHOICES)[0])
            elif type(form_field.block) is ScoreFieldWithoutTextBlock:
                update_data(
                    random.randint(form_field.value["min"], form_field.value["max"])
                )
            elif type(form_field.block) is DropdownFieldBlock:
                update_data(random.choice(form_field.value["choices"][1]))
            elif type(form_field.block) is ValueBlock:
                update_data(random.randint(0, 10000000))
            elif type(form_field.block) in [
                TextFieldBlock,
                CharFieldBlock,
                RichTextFieldBlock,  # This may need to be updated sometime in the future
                RecommendationCommentsBlock,
            ]:
                update_text_data()
            elif (
                type(form_field.block)
                in [
                    RadioButtonsFieldBlock,  # If it's a radio button, then it doesn't really need to be randomized
                    CheckboxFieldBlock,  # Similar to above
                    DurationBlock,  # Hopefully no one is encoding some super specific PII in a duration :)
                    CategoryQuestionBlock,  # Similarly, what Category should not be changed (what it if affects something else)
                    VisibilityBlock,  # Visility of reviews can remain
                ]
            ):
                pass
            else:
                print(form_holder.id)
                print(form_field.value["field_label"])
                print(data)
                raise Exception(
                    "Don't know how to handle " + str(type(form_field.block))
                )
        form_holder.save()

    def handle(self, *args, **options):
        self.f = Faker()

        for revision in ApplicationRevision.objects.all():
            self.sanitize(revision)

        for submission in ApplicationSubmission.objects.all():
            self.sanitize(submission)

        for review in Review.objects.all():
            self.sanitize(review)

        User = get_user_model()
        for user in User.objects.all():
            if options["exclude"] and user.email in options["exclude"]:
                continue
            if user.full_name:
                user.full_name = self.f.name()
            if user.slack:
                user.slack = "@" + self.f.word()
            if user.email:
                user.email = self.f.email()
            user.save()
