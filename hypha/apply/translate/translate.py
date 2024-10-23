import argostranslate.translate

from . import utils


def translate(string: str, from_code: str, to_code: str) -> str:
    """Translate a string from one language to another

    Requires the request language's argostranslate package to be installed first

    Args:
        string: the string to translate
        from_code: the ISO 639 code of the original language
        to_code: the ISO 639 code of the language to translate to

    Returns:
        str: the translated string

    Raises:
        ValueError: if the requested language translation package is not installed or request is invalid
    """

    if from_code == to_code:
        raise ValueError("Translation from_code cannot match to_code")

    available_translations = utils.get_available_translations([from_code])

    if not available_translations or to_code not in [
        package.to_code for package in available_translations
    ]:
        raise ValueError(f"Package {from_code} -> {to_code} is not installed")

    translated_text = argostranslate.translate.translate(string, from_code, to_code)

    return translated_text
