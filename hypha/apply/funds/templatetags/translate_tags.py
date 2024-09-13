import json

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from hypha.apply.translate.translate import get_available_translations
from hypha.apply.translate.utils import get_lang_name_from_code, get_translation_params

register = template.Library()


@register.simple_tag(takes_context=True)
def get_language_choices_json(context) -> str:
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
