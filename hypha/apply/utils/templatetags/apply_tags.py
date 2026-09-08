import decimal
import re
import urllib.parse

import babel.numbers
from django import template
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.files import FieldFile
from django.template.defaultfilters import stringfilter
from django.urls import reverse
from django.utils.translation import get_language

from hypha.core.navigation import get_primary_navigation_items

register = template.Library()


# Get the verbose name of a model instance
@register.filter
def model_verbose_name(instance):
    return instance._meta.verbose_name


@register.filter
def instance_verbose_name(instance):
    Report = apps.get_model("project_reports", "Report")
    Project = apps.get_model("application_projects", "Project")
    Invoice = apps.get_model("application_projects", "Invoice")
    ProjectSOW = apps.get_model("application_projects", "ProjectSOW")
    ProjectFormPointer = apps.get_model("application_projects", "ProjectFormPointer")
    if any(
        isinstance(instance, model)
        for model in [Report, Project, Invoice, ProjectSOW, ProjectFormPointer]
    ):
        return str(instance)

    return model_verbose_name(instance)


@register.filter
def is_determination(instance):
    Determination = apps.get_model("determinations", "Determination")
    return isinstance(instance, Determination)


@register.filter
def format_number_as_currency(amount: float | decimal.Decimal | str | None):
    """Formats a number as currency"""
    if amount is None:
        amount = 0

    return babel.numbers.format_currency(
        amount,
        settings.CURRENCY_CODE,
        locale=settings.CURRENCY_LOCALE,
    )


@register.simple_tag
def get_currency_symbol():
    """Gets the currency symbol based on system settings"""
    return babel.numbers.get_currency_symbol(
        settings.CURRENCY_CODE, locale=settings.CURRENCY_LOCALE
    )


@register.filter
def subtract(total_submissions: int, req_amt_submissions: int) -> int:
    """Subtracts two numbers

    Primarily used in calculating the the number of submissions to be excluded in the results view

    Args:
        total_submissions: number to be subtracted from
        req_amt_submissions: number to subtract

    Returns:
        int: the difference between the given values
    """
    return total_submissions - req_amt_submissions


@register.filter(is_safe=True)
@stringfilter
def truncatechars_middle(value, arg):
    try:
        ln = int(arg)
    except ValueError:
        return value
    if len(value) <= ln:
        return value
    else:
        return "{}...{}".format(value[: ln // 2], value[-((ln + 1) // 2) :])


@register.simple_tag
def primary_navigation_items(request):
    return get_primary_navigation_items(request)


@register.simple_tag
def does_file_exist(file: FieldFile) -> bool:
    """Check whether a file in a FieldFile actually exists"""
    return bool(file.name) and file.storage.exists(file.name)


@register.simple_tag
def generate_post_comment_url(source, related=None) -> str:
    """Takes the source + related object to generate query params for the `post-comment` url"""
    params = {}

    for obj_type, obj in {"source": source, "related": related}.items():
        if obj:
            obj_type_id = ContentType.objects.get_for_model(obj).id
            params.update(
                {
                    f"{obj_type}_content_type": obj_type_id,
                    f"{obj_type}_object_id": obj.id,
                }
            )

    return f"{reverse('activity:post-comment')}?{urllib.parse.urlencode(params)}"


CONSONANT_SOUND = re.compile(
    r"""
one(?![ir])
""",
    re.IGNORECASE | re.VERBOSE,
)
VOWEL_SOUND = re.compile(
    r"""
[aeio]|
u([aeiou]|[^n][^aeiou]|ni[^dmnl]|nil[^l])|
h(ier|onest|onou?r|ors\b|our(?!i))|
[fhlmnrsx]\b
""",
    re.IGNORECASE | re.VERBOSE,
)


def an_or_a(text):
    """
    Very English specific!

    A helper for `with_indefinite_article`, not a template filter - exposing it
    to templates invites putting a bare English article into a translatable
    string.

    Guess "a" vs "an" based on the phonetic value of the text.

    "An" is used for the following words / derivatives with an unsounded "h":
    heir, honest, hono[u]r, hors (d'oeuvre), hour

    "An" is used for single consonant letters which start with a vowel sound.

    "A" is used for appropriate words starting with "one".

    An attempt is made to guess whether "u" makes the same sound as "y" in
    "you".
    """
    if not CONSONANT_SOUND.match(text) and VOWEL_SOUND.match(text):
        return "an"
    return "a"


@register.filter
@stringfilter
def with_indefinite_article(text):
    """Prefix `text` with an indefinite article, when the active language has one.

    Composing the article and the noun here keeps the article out of the
    surrounding translatable string - `an_or_a` only knows English rules, so
    every other language gets the bare noun and lets its own translation of the
    surrounding phrase carry the grammar.
    """
    language = get_language() or settings.LANGUAGE_CODE
    if not language.lower().startswith("en"):
        return text

    return f"{an_or_a(text)} {text}"
