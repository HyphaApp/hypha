from django.test import TestCase

import factory

from opentech.apply.funds.models import FundType

from .factories import ApplicationFormFactory, FundTypeFactory, workflow_for_stages
from opentech.apply.review.tests.factories import ReviewFormFactory


def formset_base(field, total, delete, factory, same=False):
    base_data = {
        f'{field}-TOTAL_FORMS': total + delete,
        f'{field}-INITIAL_FORMS': 0,
    }

    required_forms = total + delete

    if not same:
        application_forms = factory.create_batch(required_forms)
    else:
        application_forms = [factory()] * required_forms

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


def form_data(number_forms=0, delete=0, stages=1, same_forms=False):
    form_data = formset_base('forms', number_forms, delete, same=same_forms, factory=ApplicationFormFactory)
    review_form_data = formset_base('review_forms', number_forms, False, same=same_forms, factory=ReviewFormFactory)
    form_data.update(review_form_data)

    fund_data = factory.build(dict, FACTORY_CLASS=FundTypeFactory)
    fund_data['workflow_name'] = workflow_for_stages(stages)

    form_data.update(fund_data)
    return form_data


class TestWorkflowFormAdminForm(TestCase):

    def submit_data(self, data):
        form_class = FundType.get_edit_handler().get_form_class()
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
        form = self.submit_data(form_data(2, stages=1))
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors['__all__'])
        formset_errors = form.formsets['forms'].errors
        # First form is ok
        self.assertFalse(formset_errors[0])
        # second form is too many
        self.assertTrue(formset_errors[1]['form'])

    def test_can_save_two_forms(self):
        form = self.submit_data(form_data(2))
        self.assertTrue(form.is_valid())
