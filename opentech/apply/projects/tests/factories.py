import decimal
import json

import factory
from django.utils import timezone

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.projects.models import Project
from opentech.apply.users.tests.factories import UserFactory

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


class ProjectFactory(factory.DjangoModelFactory):
    submission = factory.SubFactory(ApplicationSubmissionFactory)
    user = factory.SubFactory(UserFactory)

    title = factory.Sequence('name {}'.format)
    contact_legal_name = 'test'
    contact_email = 'test@example.com'
    contact_address = json.dumps(ADDRESS)
    contact_phone = '555 1234'
    value = decimal.Decimal('100')
    proposed_start = factory.LazyFunction(timezone.now)
    proposed_end = factory.LazyFunction(timezone.now)

    class Meta:
        model = Project
