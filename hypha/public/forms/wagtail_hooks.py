from django.contrib.contenttypes.models import ContentType

from wagtail.core import hooks

from opentech.public.forms.models import FormPage


@hooks.register('filter_form_submissions_for_user')
def construct_from_wagtail_forms(user, queryset):
    """only show wagtail forms (hiding all the ones created from the apply app)."""

    form_page_type = ContentType.objects.get_for_model(FormPage)
    queryset = queryset.filter(content_type__pk=form_page_type.pk)

    return queryset
