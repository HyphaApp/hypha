from bs4 import BeautifulSoup
from difflib import SequenceMatcher

import bleach

from django.utils.html import format_html
from django.utils.text import mark_safe


def wrap_with_span(text, class_name):
    return format_html('<div class="diff diff__{}">{}</div>', class_name, mark_safe(text))


def wrap_deleted(text):
    return wrap_with_span(text, 'deleted')


def wrap_added(text):
    return wrap_with_span(text, 'added')


def compare(answer_a, answer_b, should_bleach=True):
    if not answer_a and not answer_b:
        # This catches the case where both results are None and we cant compare
        return answer_b
    if isinstance(answer_a, dict) or isinstance(answer_b, dict):
        # TODO: handle file dictionaries
        return answer_b

    if should_bleach:
        if isinstance(answer_a, str):
            answer_a = bleach.clean(answer_a)
        else:
            answer_a = str(answer_a)

        if isinstance(answer_b, str):
            answer_b = bleach.clean(answer_b)
        else:
            answer_b = str(answer_b)

    diff = SequenceMatcher(None, answer_a, answer_b)
    output = []
    added = []
    deleted = []
    for opcode, a0, a1, b0, b1 in diff.get_opcodes():
        if opcode == 'equal':
            if a1 - a0 > 2 or not (added or deleted):
                # if there is more than 2 chars the same commit the added and removed text
                if added:
                    output.append(wrap_added(''.join(added)))
                    added = []
                if deleted:
                    output.append(wrap_deleted(''.join(deleted)))
                    deleted = []
                output.append(diff.a[a0:a1])
            else:
                # ignore the small gap pretend it has been both added and removed
                added.append(diff.a[a0:a1])
                deleted.append(diff.a[a0:a1])
        elif opcode == 'insert':
            added.append(diff.b[b0:b1])
        elif opcode == 'delete':
            deleted.append(diff.a[a0:a1])
        elif opcode == 'replace':
            deleted.append(diff.a[a0:a1])
            added.append(diff.b[b0:b1])

    # Handle text not added to the output already
    if added == deleted:
        output.append(''.join(added))
    else:
        if deleted:
            output.append(wrap_deleted(''.join(deleted)))
        if added:
            output.append(wrap_added(''.join(added)))

    display = BeautifulSoup(''.join(output)).prettify()

    return mark_safe(display)
