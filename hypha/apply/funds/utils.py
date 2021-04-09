from hypha.apply.utils.image import generate_image_tag

from .models.screening import ScreeningStatus


def render_icon(image):
    if not image:
        return ''
    filter_spec = 'fill-20x20'
    return generate_image_tag(image, filter_spec)


def get_default_screening_statues():
    """
    Get the default Screening decisions set.

    If the default for yes and no doesn't exit. First yes and
    first no Screening decisions created should be set as default
    """
    yes_screening_statuses = ScreeningStatus.objects.filter(yes=True)
    no_screening_statuses = ScreeningStatus.objects.filter(yes=False)
    default_yes = None
    default_no = None
    if yes_screening_statuses.exists():
        try:
            default_yes = yes_screening_statuses.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first yes Screening decision as default
            default_yes = yes_screening_statuses.first()
            default_yes.default = True
            default_yes.save()
    if no_screening_statuses.exists():
        try:
            default_no = no_screening_statuses.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first no Screening decision as default
            default_no = no_screening_statuses.first()
            default_no.default = True
            default_no.save()
    return [default_yes, default_no]
