import re
from difflib import SequenceMatcher
from typing import Tuple

import nh3
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def wrap_deleted(text):
    return format_html(
        '<span class="bg-red-200 line-through">{}</span>', mark_safe(text)
    )


def wrap_added(text):
    return format_html('<span class="bg-green-200">{}</span>', mark_safe(text))


def compare(answer_a: str, answer_b: str, should_clean: bool = True) -> Tuple[str, str]:
    """Compare two strings, populate diff HTML and insert it, and return a tuple of the given strings.

    Args:
        answer_a:
            The original string
        answer_b:
            The string to compare to the original
        should_clean:
            Optional boolean to determine if the string should be sanitized with NH3 (default=True)

    Returns:
        A tuple of the original strings with diff HTML inserted.
    """

    if should_clean:
        answer_a = re.sub("(<li[^>]*>)", r"\1◦ ", answer_a)
        answer_b = re.sub("(<li[^>]*>)", r"\1◦ ", answer_b)
        answer_a = nh3.clean(answer_a, tags={"h4"}, attributes={})
        answer_b = nh3.clean(answer_b, tags={"h4"}, attributes={})

    diff = SequenceMatcher(None, answer_a, answer_b)
    from_diff = []
    to_diff = []
    for opcode, a0, a1, b0, b1 in diff.get_opcodes():
        if opcode == "equal":
            from_diff.append(mark_safe(diff.a[a0:a1]))
            to_diff.append(mark_safe(diff.b[b0:b1]))
        elif opcode == "insert":
            from_diff.append(mark_safe(diff.a[a0:a1]))
            to_diff.append(wrap_added(diff.b[b0:b1]))
        elif opcode == "delete":
            from_diff.append(wrap_deleted(diff.a[a0:a1]))
            to_diff.append(mark_safe(diff.b[b0:b1]))
        elif opcode == "replace":
            from_diff.append(wrap_deleted(diff.a[a0:a1]))
            to_diff.append(wrap_added(diff.b[b0:b1]))

    from_display = "".join(from_diff)
    to_display = "".join(to_diff)
    from_display = re.sub("(\\.\n)", r"\1<br><br>", from_display)
    to_display = re.sub("(\\.\n)", r"\1<br><br>", to_display)
    from_display = re.sub(r"([◦])", r"<br>\1", from_display)
    to_display = re.sub(r"([◦])", r"<br>\1", to_display)
    from_display = mark_safe(from_display)
    to_display = mark_safe(to_display)

    return (from_display, to_display)
