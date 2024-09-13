import json

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from hypha.apply.translate.translate import get_available_translations
from hypha.apply.translate.utils import get_lang_name_from_code, get_translation_params

register = template.Library()


@register.simple_tag(takes_context=True)
def get_language_choices_json(context: dict) -> str:
    """Generate a JSON output of available translation options

    Args:
        context: the context of the template, containing an `HttpRequest` key & object

    Returns:
        A JSON string in the format of:

        ```
        [
            {
                "code": "<from language code>",
                "name": "<from language name>",
                "to": [
                    {
                        "code": "<to language code>",
                        "name": "<from language name>"
                    }
                ],
                "selectedTo": "<selected to language if any>",
                "selected": bool if selected by default
            },
            ...
        ]
        ```
    """
    available_translations = get_available_translations()
    from_langs = {package.from_code for package in available_translations}
    default_to_lang = settings.LANGUAGE_CODE
    default_from_lang = None

    # If there's existing lang params, use those as the default in the form
    if (current_url := context["request"].headers.get("Hx-Current-Url")) and (
        params := get_translation_params(current_url)
    ):
        default_from_lang, default_to_lang = params

    choices = []
    for lang in from_langs:
        to_langs = [
            package.to_code
            for package in available_translations
            if package.from_code == lang
        ]
        choices.append(
            {
                "code": lang,
                "name": get_lang_name_from_code(lang),
                "to": [
                    {"code": to_lang, "name": get_lang_name_from_code(to_lang)}
                    for to_lang in to_langs
                ],
                "selectedTo": default_to_lang if default_to_lang in to_langs else None,
                "selected": lang == default_from_lang,
            }
        )

    return mark_safe(json.dumps(choices))


@register.filter
def can_translate_submission(user) -> bool:
    """Verify that system settings & user role allows for submission translations.

    Args:
        user: the user to check the role of.

    Returns:
        bool: true if submission can be translated, false if not.

    """
    return bool(settings.ALLOW_SUBMISSION_TRANSLATIONS and user.is_org_faculty)
