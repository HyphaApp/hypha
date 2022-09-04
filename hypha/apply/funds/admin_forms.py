from collections import Counter

from django.apps import apps
from wagtail.admin.forms import WagtailAdminModelForm, WagtailAdminPageForm

from .models.submissions import ApplicationSubmission
from .workflow import WORKFLOWS


class WorkflowFormAdminForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()

        workflow = WORKFLOWS[cleaned_data['workflow_name']]
        application_forms = self.formsets['forms']
        review_forms = self.formsets['review_forms']
        external_review_forms = self.formsets['external_review_forms']
        determination_forms = self.formsets['determination_forms']
        number_of_stages = len(workflow.stages)

        self.validate_application_forms(workflow, application_forms)
        if number_of_stages == 1:
            self.validate_stages_equal_forms(workflow, application_forms)
        self.validate_stages_equal_forms(workflow, review_forms, form_type="Review form")
        self.validate_stages_equal_forms(workflow, external_review_forms, form_type="External Review form")
        self.validate_stages_equal_forms(
            workflow, determination_forms, form_type="Determination form"
        )

        return cleaned_data

    def validate_application_forms(self, workflow, forms):
        """
        Application forms are not equal to the number of stages like review forms.
        Now, staff can select a proposal form from multiple forms list in stage 2.
        """
        if forms.is_valid():
            valid_forms = [form for form in forms if not form.cleaned_data['DELETE']]
            forms_stages = [form.cleaned_data['stage'] for form in valid_forms]
            stages_counter = Counter(forms_stages)

            number_of_stages = len(workflow.stages)
            error_list = []

            for stage in range(1, number_of_stages + 1):
                is_form_present = True if stages_counter.get(stage, 0) > 0 else False
                if not is_form_present:
                    error_list.append(f'Please provide form for Stage {stage}.')

                if stage == 1 and stages_counter.get(stage, 0) > 1:
                    error_list.append('Only 1 form can be selected for 1st Stage.')

            if error_list:
                self.add_error(
                    None,
                    error_list,
                )

    def validate_stages_equal_forms(self, workflow, forms, form_type="form"):
        if forms.is_valid():
            valid_forms = [form for form in forms if not form.cleaned_data['DELETE']]
            number_of_forms = len(valid_forms)
            plural_form = 's' if number_of_forms > 1 else ''

            number_of_stages = len(workflow.stages)
            plural_stage = 's' if number_of_stages > 1 else ''

            # External Review Form is optional and should be single if provided
            if form_type == "External Review form":
                if number_of_forms > 1:
                    self.add_error(
                        None,
                        f'Number of {form_type}s should not be more than one: '
                        f'{number_of_forms} {form_type}{plural_form} provided',
                    )
                    return
                else:
                    return

            if number_of_forms != number_of_stages:
                self.add_error(
                    None,
                    f'Number of {form_type}s does not match number of stages: '
                    f'{number_of_stages} stage{plural_stage} and {number_of_forms} '
                    f'{form_type}{plural_form} provided',
                )

                for form in valid_forms[number_of_stages:]:
                    form.add_error('form', 'Exceeds required number of forms for stage, please remove.')


class RoundBasePageAdminForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data['start_date']
        if not start_date:
            self.add_error('start_date', 'Please select start date.')

        return cleaned_data


class ScreeningStatusAdminForm(WagtailAdminModelForm):

    def save(self, commit=True):
        default = self.cleaned_data['default']
        yes = self.cleaned_data['yes']
        ScreeningStatus = apps.get_model('funds', 'ScreeningStatus')
        if default:
            try:
                default_screening = ScreeningStatus.objects.get(
                    default=default, yes=yes
                )
            except ScreeningStatus.DoesNotExist:
                pass
            else:
                screening = super().save(commit)
                if default_screening.id != screening.id:
                    submissions = ApplicationSubmission.objects.filter(screening_statuses__id=default_screening.id)
                    for submission in submissions:
                        submission.screening_statuses.remove(default_screening)
                        submission.screening_statuses.add(screening)
                    default_screening.default = False
                    default_screening.save()
                return screening
        return super().save(commit)
