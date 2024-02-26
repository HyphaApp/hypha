from itertools import chain

from hypha.apply.utils.image import generate_image_tag

from .models.screening import ScreeningStatus


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


status_and_phases_mapping = {
    "received": ["need-screening", "proposal-received"],
    "in-discussion": ["ready-for-discussion"],
    "internal-review": ["internal-review"],
    "more-information": ["more-information-required"],
    "invited-for-proposal": ["invited-for-proposal"],
    "external-review": ["external-review"],
    "ready-for-determination": [
        "ready-for-determination",
        "ready-for-preliminary-determination",
        "ready-for-final-determination",
    ],
    "accepted": ["accepted"],
    "dismissed": ["dismissed"],
}


def get_statuses_as_params(statuses):
    params = "?"
    for status in statuses:
        params += "status=" + status + "&"
    return params
