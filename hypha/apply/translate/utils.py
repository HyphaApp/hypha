import json
import re
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import argostranslate
from bs4 import BeautifulSoup, element
from django.conf import settings
from django.http import HttpRequest

from . import translate


def get_available_translations(
    from_codes: Optional[List[str]] = None,
) -> List[argostranslate.package.Package]:
    """Get languages available for translation

    Args:
        from_codes: optionally specify a list of languages to view available translations to

    Returns:
        A list of argostranslate package objects that are installed and available.
    """

    available_packages = argostranslate.package.get_installed_packages()

    if not from_codes:
        return available_packages

    return list(filter(lambda x: x.from_code in from_codes, available_packages))


def get_translation_params(
    url: str = None, request: HttpRequest = None
) -> Tuple[str, str] | None:
    r"""Attempts to extract the `fl` (from language) & `tl` (to language) params from the provided URL or request object

    Return values are *not* validated to ensure languages are valid & packages exist.

    Args:
        url: the URL to extract the params from

    Returns:
        tuple: in the format of (\<from langauge\>, \<to language\>)

    Raises:
        ValueError: If `url`/`request` are not provided OR if both are provided
    """

    # Ensure either url or request is provided but not both.
    if not (bool(url) ^ bool(request)):
        raise ValueError("Either a URL or HttpRequest must be provided.")

    if url:
        query_dict = {k: v[0] for (k, v) in parse_qs(urlparse(url).query).items()}
    else:
        query_dict = request.GET

    if (to_lang := query_dict.get("tl")) and (from_lang := query_dict.get("fl")):
        return (from_lang, to_lang)

    return None


def get_lang_name(code: str) -> str | None:
    try:
        return argostranslate.translate.get_language_from_code(code).name
    except AttributeError:
        return None


def get_language_choices_json(request: HttpRequest) -> str:
    """Generate a JSON output of available translation options

    Utilized for populating the reactive form fields on the client side

    Args:
        request: an `HttpRequest` containing an "Hx-Current-Url" header to extract current translation params from

    Returns:
        A JSON string in the format of:

        ```
        [
            {
                "value": "<from language code>",
                "label": "<from language name>",
                "to": [
                    {
                        "value": "<to language code>",
                        "label": "<from language name>"
                        "selected": <bool if selected by default>
                    }
                ],
                "selected": <bool if selected by default>
            },
            ...
        ]
        ```
    """
    available_translations = get_available_translations()
    from_langs = {package.from_code for package in available_translations}
    default_to_lang = settings.LANGUAGE_CODE if settings.LANGUAGE_CODE else None
    default_from_lang = None

    # If there's existing lang params, use those as the default in the form
    # ie. the user has an active translation for ar -> en, those should be selected in the form
    if (current_url := request.headers.get("Hx-Current-Url")) and (
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

        # Set the default selection to be the default_to_lang if it exists in the to_langs list,
        # otherwise use the first value in the list.
        selected_to = (
            default_to_lang
            if default_to_lang and default_to_lang in to_langs
            else to_langs[0]
        )

        to_choices = [
            {
                "value": to_lang,
                "label": get_lang_name(to_lang),
                "selected": to_lang == selected_to,
            }
            for to_lang in to_langs
        ]

        choices.append(
            {
                "value": lang,
                "label": get_lang_name(lang),
                "to": to_choices,
                "selected": lang == default_from_lang,
            }
        )

    return json.dumps(choices)


def translate_application_form_data(application, from_code: str, to_code: str) -> dict:
    """Translate the content of an application's live revision `form_data`.
    Will parse fields that contain both plaintext & HTML, extracting & replacing strings.

    NOTE: Mixed formatting like `<p>Hey from <strong>Hypha</strong></p>` will result in a
    string that is stripped of text formatting (untranslated: `<p>Hey from Hypha</p>`). On
    the other hand, unmixed strings like `<p><strong>Hey from Hypha</strong></p>` will be
    replaced within formatting tags.

    Args:
        application: the  application to translate
        from_code: the ISO 639 code of the original language
        to_code: the ISO 639 code of the language to translate to

    Returns:
        The `form_data` with values translated (including nested HTML strings)

    Raises:
        ValueError if an invalid `from_code` or `to_code` is requested
    """
    form_data: dict = application.live_revision.form_data

    translated_form_data = form_data.copy()

    # Only translate content fields or the title - don't with name, email, etc.
    translated_form_data["title"] = translate.translate(
        form_data["title"], from_code, to_code
    )

    # RegEx to match wagtail's generated field UIDs - ie. "97c51cea-ab47-4a64-a64a-15d893788ef2"
    uid_regex = re.compile(r"([a-z]|\d){8}(-([a-z]|\d){4}){3}-([a-z]|\d){12}")
    fields_to_translate = [
        key
        for key in form_data
        if uid_regex.match(key) and isinstance(form_data[key], str)
    ]

    for key in fields_to_translate:
        field_html = BeautifulSoup(form_data[key], "html.parser")
        if field_html.find():  # Check if BS detected any HTML
            for field in field_html.find_all(has_valid_str):
                # Removes formatting if mixed into the tag to prioritize context in translation
                # ie. `<p>Hey <strong>y'all</strong></p>` -> `<p>Hey y'all</p>` (but translated)
                to_translate = field.string if field.string else field.text
                field.clear()
                field.string = translate.translate(to_translate, from_code, to_code)

            translated_form_data[key] = str(field_html)
        # Ensure the field value isn't empty & translate as is
        elif form_data[key].strip():
            translated_form_data[key] = translate.translate(
                form_data[key], from_code, to_code
            )

    return translated_form_data


def has_valid_str(tag: element.Tag) -> bool:
    """Checks that an Tag contains a valid text element and/or string.

    Args:
        tag: a `bs4.element.Tag`
    Returns:
        bool: True if has a valid string that isn't whitespace or `-`
    """
    text_elem = tag.name in ["span", "p", "strong", "em", "td", "a"]

    try:
        # try block logic handles elements that have text directly in them
        # ie. `<p>test</p>` or `<em>yeet!</em>` would return true as string values would be contained in tag.string
        ret = bool(
            text_elem
            and tag.find(string=True, recursive=False)
            and tag.string.strip(" -\n")
        )
        return ret
    except AttributeError:
        # except block logic handles embedded tag strings where tag.string == None but the specified tag DOES contain a string
        # ie. `<p>Hypha is <strong>cool</strong></p>` contains the string "Hypha is" but due to the strong tag being mixed in will
        # have None for the tag.string value.
        # tags like `<p> <em>Hypha rocks</em> </p>` will return false as the <p> tag contains no valid strings, it's child does.
        tag_contents = "".join(tag.find_all(string=True, recursive=False))
        ret = bool(tag.text and tag.text.strip() and tag_contents.strip())
        return ret
