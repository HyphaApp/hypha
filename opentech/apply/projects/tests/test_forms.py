from django.test import TestCase

from ..forms import ProjectEditForm
from .factories import ProjectFactory, address_to_form_data


class TestProjectEditForm(TestCase):
    def test_updating_fields_sets_changed_flag(self):
        project = ProjectFactory()

        self.assertFalse(project.user_has_updated_details)

        data = {
            'title': f'{project.title} test',
            'contact_legal_name': project.contact_legal_name,
            'contact_email': project.contact_email,
            'contact_phone': project.contact_phone,
            'value': project.value,
            'proposed_start': project.proposed_start,
            'proposed_end': project.proposed_end,
        }
        data.update(address_to_form_data())
        form = ProjectEditForm(instance=project, data=data)
        form.save()

        self.assertTrue(project.user_has_updated_details)
