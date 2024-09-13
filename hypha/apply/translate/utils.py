from typing import Tuple
from urllib.parse import parse_qs, urlparse

import argostranslate.translate
from django.http import HttpRequest


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


def get_lang_name_from_code(from_code: str) -> str | None:
    try:
        return argostranslate.translate.get_language_from_code(from_code).name
    except AttributeError:
        return None
