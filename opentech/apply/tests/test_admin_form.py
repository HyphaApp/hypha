from django.test import TestCase

import factory

from opentech.apply.models import FundPage

from .factories import ApplicationFormFactory, FundPageFactory


def formset_base(field, total, delete):
    base_data = {
        f'{field}-TOTAL_FORMS': total + delete,
        f'{field}-INITIAL_FORMS': 0,
    }
    application_forms = ApplicationFormFactory.create_batch(total + delete)

    deleted = 0
    for i, form in enumerate(application_forms):
        should_delete = deleted < delete
        base_data.update({
            f'{field}-{i}-form': form.id,
            f'{field}-{i}-ORDER': i,
            f'{field}-{i}-DELETE': should_delete,
        })
        deleted += 1

    return base_data


def form_data(number_forms=0, delete=0):
    base_data = formset_base('forms', number_forms, delete)
    base_data.update(factory.build(dict, FACTORY_CLASS=FundPageFactory))
    return base_data


class TestWorkflowFormAdminForm(TestCase):

    def submit_data(self, data):
        form_class = FundPage.get_edit_handler().get_form_class(FundPage)
        return form_class(data=data)

    def test_doesnt_validates_with_no_form(self):
        form = self.submit_data(form_data())
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors['__all__'])

    def test_validates_with_one_form_one_stage(self):
        form = self.submit_data(form_data(1))
        self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_validates_with_one_form_one_stage_with_deleted(self):
        form = self.submit_data(form_data(1, delete=1))
        self.assertTrue(form.is_valid(), form.errors.as_text())

    def test_doesnt_validates_with_two_forms_one_stage(self):
        form = self.submit_data(form_data(2))
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors['__all__'])
        formset_errors = form.formsets['forms'].errors
        # First form is ok
        self.assertFalse(formset_errors[0])
        # second form is too many
        self.assertTrue(formset_errors[1]['form'])
