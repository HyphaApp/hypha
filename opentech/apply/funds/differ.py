from bleach.sanitizer import Cleaner
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

from django.utils.html import format_html
from django.utils.safestring import mark_safe


def wrap_with_span(text, class_name):
    return format_html('<span class="diff diff__{}">{}</span>', class_name, mark_safe(text))


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
        cleaner = Cleaner(tags=['h4'], attributes={}, strip=True)
        if isinstance(answer_a, str):
            answer_a = cleaner.clean(answer_a)
        else:
            answer_a = str(answer_a)

        if isinstance(answer_b, str):
            answer_b = cleaner.clean(answer_b)
        else:
            answer_b = str(answer_b)

    diff = SequenceMatcher(None, answer_a, answer_b)
    output = []
    added = []
    deleted = []
    for opcode, a0, a1, b0, b1 in diff.get_opcodes():
        if opcode == 'equal':
            if a1 - a0 > 2 or not (added or deleted):
                # if there are more than two of the same characters, commit the added and removed text
                if added:
                    output.append(wrap_added(''.join(added)))
                    added = []
                if deleted:
                    output.append(wrap_deleted(''.join(deleted)))
                    deleted = []
                output.append(diff.a[a0:a1])
            else:
                # Ignore the small gap pretend it has been both added and removed
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

    display = ''.join(output)

    if not should_bleach:
        soup = BeautifulSoup(display, "html5lib")
        soup.body.hidden = True
        display = soup.body.prettify()

    return mark_safe(display)
