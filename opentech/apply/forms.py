from django import forms
from wagtail.wagtailadmin.forms import WagtailAdminPageForm


class WorkflowFormAdminForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()

        model= self._meta.model

        from .models import WORKFLOW_CLASS
        workflow = WORKFLOW_CLASS[model.WORKFLOWS[cleaned_data['workflow']]]
        number_of_stages = len(workflow.stage_classes)
        number_of_forms = len(cleaned_data['forms'])

        plural_stage = 's' if number_of_stages > 1 else ''
        plural_form = 's' if number_of_stages > 1 else ''

        if number_of_forms != number_of_stages:
            self.add_error(
                None,
                'Number of forms does not match number of stages: '
                f'{number_of_stages} stage{plural_stage} and {number_of_forms} '
                f'form{plural_form} provided',
            )

        return cleaned_data
