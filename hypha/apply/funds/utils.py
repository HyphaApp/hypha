import csv
import re
from datetime import datetime
from functools import reduce
from io import StringIO
from itertools import chain
from operator import iconcat
from typing import Iterable

import django_filters as filters
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

# from django.contrib.sites.models import Site
from hypha.apply.funds.models.submissions import ApplicationSubmission
from hypha.apply.users.tokens import CoApplicantInviteTokenGenerator
from hypha.apply.utils.image import generate_image_tag

from .models.screening import ScreeningStatus


def render_icon(image):
    if not image:
        return ""
    filter_spec = "fill-20x20"
    return generate_image_tag(image, filter_spec, html_class="size-4")


def get_or_create_default_screening_statuses(
    yes_screen_status_qs, no_screening_status_qs
):
    """
    Get the default screening decisions set.

    If the default for yes and no doesn't exit. First yes and
    first no screening decisions created should be set as default
    """
    default_yes = None
    default_no = None
    if yes_screen_status_qs.exists():
        try:
            default_yes = yes_screen_status_qs.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first yes screening decision as default
            default_yes = yes_screen_status_qs.first()
            default_yes.default = True
            default_yes.save()
    if no_screening_status_qs.exists():
        try:
            default_no = no_screening_status_qs.get(default=True)
        except ScreeningStatus.DoesNotExist:
            # Set first no screening decision as default
            default_no = no_screening_status_qs.first()
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


def export_submissions_to_csv(
    submissions_list: Iterable[ApplicationSubmission], base_uri: str
):
    csv_stream = StringIO()
    header_row = ["Application #", "URL"]
    index = 2
    data_list = []

    for submission in submissions_list:
        values = {}
        values["Application #"] = submission.id
        values["URL"] = f"{base_uri}{submission.get_absolute_url().lstrip('/')}"
        for field_id in submission.question_text_field_ids:
            question_field = submission.serialize(field_id)
            field_name = question_field["question"]
            field_value = question_field["answer"]
            if field_id == "address" and isinstance(field_value, dict):
                address = []
                for key, value in field_value.items():
                    address.append(f"{key}: {value}")
                field_value = "\n".join(address)
            if field_name not in header_row:
                if field_id not in submission.named_blocks:
                    header_row.append(field_name)
                else:
                    header_row.insert(index, field_name)
                    index = index + 1
            values[field_name] = strip_tags(field_value)
        data_list.append(values)
    writer = csv.DictWriter(csv_stream, fieldnames=header_row, restval="")
    writer.writeheader()
    for data in data_list:
        writer.writerow(data)
    csv_stream.seek(0)
    return csv_stream


def format_submission_sum_value(submission_value: dict) -> str | None:
    """Formats a submission value dict that contains a key of `value__sum`

    Args:
        submission_value: the dict containing the `value_sum`

    Returns:
        either a string of the formatted sum value or `None` if invalid
    """

    value_sum = submission_value.get("value__sum")

    return value_sum if value_sum else None


def is_filter_empty(filter: filters.FilterSet) -> bool:
    """Determines if a given FilterSet has valid query params or if they're empty

    Args:
        filter: the FilterSet to evaluate

    Returns:
        bool: True if filter has valid params, False if empty
    """

    if not (query := filter.data):
        return False

    # Flatten the QueryDict values in filter.data to a single list, check for validity with any()
    return any(reduce(iconcat, [param[1] for param in query.lists()], []))


def get_copied_form_name(original_form_name: str) -> str:
    """Create the name of the form to be copied

    By default, takes the original forms name and adds `(Copied on %Y-%m-%d %H:%M:%S.%f)`

    If a timestamp exists on the original_form_name, it will be replaced.
    This works even if the `Copied on` string is translated.

    Args:
        original_form_name: the name of the form being duplicated

    Returns:
        str: name of the copied form
    """
    copy_str = _("Copied on {copy_time}")
    copy_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
    date_reg = r"(\d{2,4}-?){3} (\d{2}(:|.)?){4}"  # match the strftime pattern of %Y-%m-%d %H:%M:%S.%f

    # Escape the `copy_str` to allow for translations to be matched & replace the
    # `{copy_time}` var with the `date_reg` regex
    name_reg = r" \({}\)$".format(
        re.escape(copy_str).replace(r"\{copy_time\}", date_reg)
    )

    # If a copied timestamp already exists, remove it
    new_name = re.sub(name_reg, "", original_form_name)
    return f"{new_name} ({copy_str.format(copy_time=copy_time)})"


def check_submissions_same_determination_form(submissions):
    """
    Checks if all the submission have same determination forms.

    We can not create batch determination with submissions using two different
    type of forms.
    """

    same_form = True
    try:
        # check form id
        determination_form_ids = [
            submission.get_from_parent("determination_forms").first().id
            for submission in submissions
        ]
    except Exception:
        # if there is a form id error, handles old determination form issues
        same_form = False
        return same_form

    if any(d_id != determination_form_ids[0] for d_id in determination_form_ids):
        same_form = False
    return same_form


def get_export_polling_time(submission_count: int) -> int:
    """Get the export polling interval based on the amount of submissions being exported

    Used for checking on the completion of an export while trying to prevent unneeded
    traffic with larger exports. Division constant is based on timing trials of
    different submission sets

    Args:
        submission_count: The number of submissions being exported

    Returns:
        A polling interval in seconds, which is never smaller than 2 or larger than 45
    """
    min_interval = 2
    max_interval = 45
    interval = round(submission_count / 150)

    if min_interval < interval < max_interval:
        return interval
    elif min_interval > interval:
        return min_interval
    else:
        return max_interval


def generate_invite_path(invite):
    token = CoApplicantInviteTokenGenerator().make_token(invite)
    uid = urlsafe_base64_encode(force_bytes(invite.pk))
    login_path = reverse(
        "apply:submissions:accept_coapplicant_invite",
        kwargs={"uidb64": uid, "token": token},
    )
    return login_path
