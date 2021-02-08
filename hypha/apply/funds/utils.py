from hypha.apply.categories.blocks import CategoryQuestionBlock
from hypha.apply.categories.models import Option
from hypha.apply.utils.image import generate_image_tag

from .models.screening import ScreeningStatus

from.models.submissions import ApplicationSubmission


def render_icon(image):
    if not image:
        return ''
    filter_spec = 'fill-20x20'
    return generate_image_tag(image, filter_spec)


def get_default_screening_statues():
    """
    Get the default screening statuses set.

    If the default for yes and no doesn't exit. First yes and
    first no screening statuses created should be set as default
    """
    yes_screening_statuses = ScreeningStatus.objects.filter(yes=True)
    no_screening_statuses = ScreeningStatus.objects.filter(yes=False)
    default_yes = None
    default_no = None
    if yes_screening_statuses.exists():
        try:
            default_yes = yes_screening_statuses.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first yes screening status as default
            default_yes = yes_screening_statuses.first()
            default_yes.default = True
            default_yes.save()
    if no_screening_statuses.exists():
        try:
            default_no = no_screening_statuses.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first no screening status as default
            default_no = no_screening_statuses.first()
            default_no.default = True
            default_no.save()
    return [default_yes, default_no]


def get_category_options():
    """
    Get all category options to show as filter options in the submission table.

    - Only show options for the Category which has filter_on_dashboard set as True.
    - And only show options which are used in submissions:
      - To get this we need to first get all ApplicationSubmission form_data and form_fields.
      - Then in form_fields we need to check for Category Fields by checking the instance of CategoryQuestionBlock
      - With the field ids get the correct options selected in form_data
      - Use the list of correct option to filter options

    return: list of set of suitable category options
    """
    submission_data = ApplicationSubmission.objects.values('form_data', 'form_fields')
    used_category_options = []
    for item in submission_data:
        for field in item['form_fields']:
            if isinstance(field.block, CategoryQuestionBlock):
                used_category_options.append(item['form_data'].get(field.id, 0))
    options = Option.objects.filter(
        category__filter_on_dashboard=True,
        id__in=used_category_options
    )
    return [(option.id, option.value) for option in options]
