from itertools import chain

from django.db.models import Count
from django.urls import reverse_lazy
from django.utils.text import slugify

from hypha.apply.utils.image import generate_image_tag

from .models.applications import ApplicationSubmission
from .models.screening import ScreeningStatus
from .workflow import STATUSES


def render_icon(image):
    if not image:
        return ""
    filter_spec = "fill-20x20"
    return generate_image_tag(image, filter_spec, html_class="icon mr-2 align-middle")


def get_default_screening_statues():
    """
    Get the default screening decisions set.

    If the default for yes and no doesn't exit. First yes and
    first no screening decisions created should be set as default
    """
    yes_screening_statuses = ScreeningStatus.objects.filter(yes=True)
    no_screening_statuses = ScreeningStatus.objects.filter(yes=False)
    default_yes = None
    default_no = None
    if yes_screening_statuses.exists():
        try:
            default_yes = yes_screening_statuses.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first yes screening decision as default
            default_yes = yes_screening_statuses.first()
            default_yes.default = True
            default_yes.save()
    if no_screening_statuses.exists():
        try:
            default_no = no_screening_statuses.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first no screening decision as default
            default_no = no_screening_statuses.first()
            default_no.default = True
            default_no.save()
    return [default_yes, default_no]


def model_form_initial(instance, fields=None, exclude=None):
    """
    This is a copy of django.forms.models.model_to_dict from the django version 2.2.x.
    It helps to provide initial to BaseModelForm with fields as empty list[].

    Return a dict containing the data in ``instance`` suitable for passing as
    a Model Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    """
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if not getattr(f, "editable", False):
            continue
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)
    return data


def get_applications_status_counts(current_url_queries):
    application_status_url_query = current_url_queries.get("status")
    status_counts = dict(
        ApplicationSubmission.objects.current()
        .values("status")
        .annotate(
            count=Count("status"),
        )
        .values_list("status", "count")
    )

    grouped_statuses = {
        name: {
            "name": name,
            "count": sum(status_counts.get(status, 0) for status in statuses),
            "url": reverse_lazy("funds:submissions:list") + "?status=" + slugify(name),
            "is_active": True
            if application_status_url_query
            and slugify(name) in application_status_url_query
            else False,
        }
        for name, statuses in STATUSES.items()
    }
    return grouped_statuses
