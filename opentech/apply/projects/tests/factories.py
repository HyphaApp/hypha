import decimal
import json

import factory
import pytz
from django.utils import timezone

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.projects.models import (
    Contract,
    DocumentCategory,
    PacketFile,
    PaymentReceipt,
    PaymentRequest,
    Project,
    ProjectApprovalForm,
)
from opentech.apply.stream_forms.testing.factories import FormDataFactory, FormFieldsBlockFactory
from opentech.apply.users.tests.factories import StaffFactory, UserFactory

ADDRESS = {
    'country': 'GB',
    'thoroughfare': factory.Faker('street_name').generate({}),
    'premise': factory.Faker('building_number').generate({}),
    'locality': {
        'localityname': factory.Faker('city').generate({}),
        'administrativearea': factory.Faker('city').generate({}),
        'postal_code': 'SW1 4AQ',
    }
}


def address_to_form_data():
    """
    Generate a AddressField compatible dictionary from the address data
    """
    return {
        'contact_address_0': ADDRESS['country'],
        'contact_address_1': ADDRESS['thoroughfare'],
        'contact_address_2': ADDRESS['premise'],
        'contact_address_3_0': ADDRESS['locality']['localityname'],
        'contact_address_3_1': ADDRESS['locality']['administrativearea'],
        'contact_address_3_2': ADDRESS['locality']['postal_code'],
    }


class DocumentCategoryFactory(factory.DjangoModelFactory):
    name = factory.Sequence('name {}'.format)
    recommended_minimum = 1

    class Meta:
        model = DocumentCategory


class ProjectApprovalFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ProjectApprovalForm

    name = factory.Faker('word')
    form_fields = FormFieldsBlockFactory


class ProjectApprovalFormDataFactory(FormDataFactory):
    field_factory = FormFieldsBlockFactory


class ProjectFactory(factory.DjangoModelFactory):
    submission = factory.SubFactory(ApplicationSubmissionFactory)
    user = factory.SubFactory(UserFactory)

    title = factory.Sequence('name {}'.format)
    lead = factory.SubFactory(StaffFactory)
    contact_legal_name = 'test'
    contact_email = 'test@example.com'
    contact_address = json.dumps(ADDRESS)
    contact_phone = '555 1234'
    value = decimal.Decimal('100')
    proposed_start = factory.LazyFunction(timezone.now)
    proposed_end = factory.LazyFunction(timezone.now)

    is_locked = False

    form_fields = FormFieldsBlockFactory
    form_data = factory.SubFactory(
        ProjectApprovalFormDataFactory,
        form_fields=factory.SelfAttribute('..form_fields'),
    )

    class Meta:
        model = Project

    class Params:
        in_approval = factory.Trait(
            is_locked=True,
        )


class ContractFactory(factory.DjangoModelFactory):
    approver = factory.SubFactory(StaffFactory)
    project = factory.SubFactory(ProjectFactory)

    file = factory.django.FileField()

    class Meta:
        model = Contract


class PacketFileFactory(factory.DjangoModelFactory):
    category = factory.SubFactory(DocumentCategoryFactory)
    project = factory.SubFactory(ProjectFactory)

    title = factory.Sequence('name {}'.format)
    document = factory.django.FileField()

    class Meta:
        model = PacketFile


class PaymentRequestFactory(factory.DjangoModelFactory):
    project = factory.SubFactory(ProjectFactory)
    by = factory.SubFactory(UserFactory)
    requested_value = factory.Faker('pydecimal', min_value=1, max_value=10000000, right_digits=2)

    date_from = factory.Faker('date_time').generate({'tzinfo': pytz.utc})
    date_to = factory.Faker('date_time').generate({'tzinfo': pytz.utc})

    invoice = factory.django.FileField()

    class Meta:
        model = PaymentRequest


class PaymentReceiptFactory(factory.DjangoModelFactory):
    payment_request = factory.SubFactory(PaymentRequestFactory)

    file = factory.django.FileField()

    class Meta:
        model = PaymentReceipt
