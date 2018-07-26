from wagtail.admin.forms import WagtailAdminPageForm

from .workflow import WORKFLOWS


class WorkflowFormAdminForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()

        workflow = WORKFLOWS[cleaned_data['workflow_name']]
        application_forms = self.formsets['forms']
        review_forms = self.formsets['review_forms']

        self.validate_stages_equal_forms(workflow, application_forms)
        self.validate_stages_equal_forms(workflow, review_forms, form_type="Review form")

        return cleaned_data

    def validate_stages_equal_forms(self, workflow, forms, form_type="form"):
        if forms.is_valid():
            valid_forms = [form for form in forms if not form.cleaned_data['DELETE']]
            number_of_forms = len(valid_forms)
            plural_form = 's' if number_of_forms > 1 else ''

            number_of_stages = len(workflow.stages)
            plural_stage = 's' if number_of_stages > 1 else ''

            if number_of_forms != number_of_stages:
                self.add_error(
                    None,
                    f'Number of {form_type}s does not match number of stages: '
                    f'{number_of_stages} stage{plural_stage} and {number_of_forms} '
                    f'{form_type}{plural_form} provided',
                )

                for form in valid_forms[number_of_stages:]:
                    form.add_error('form', 'Exceeds required number of forms for stage, please remove.')
