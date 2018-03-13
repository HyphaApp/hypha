from wagtail.admin.forms import WagtailAdminPageForm


class WorkflowFormAdminForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()
        model = self._meta.model

        workflow = model.workflow_class_from_name(cleaned_data['workflow_name'])
        application_forms = self.formsets['forms']

        self.validate_stages_equal_forms(workflow, application_forms)

        return cleaned_data

    def validate_stages_equal_forms(self, workflow, application_forms):
        if application_forms.is_valid():
            valid_forms = [form for form in application_forms if not form.cleaned_data['DELETE']]
            number_of_forms = len(valid_forms)
            plural_form = 's' if number_of_forms > 1 else ''

            number_of_stages = len(workflow.stage_classes)
            plural_stage = 's' if number_of_stages > 1 else ''

            if number_of_forms != number_of_stages:
                self.add_error(
                    None,
                    'Number of forms does not match number of stages: '
                    f'{number_of_stages} stage{plural_stage} and {number_of_forms} '
                    f'form{plural_form} provided',
                )

                for form in valid_forms[number_of_stages:]:
                    form.add_error('form', 'Exceeds required number of forms for stage, please remove.')
