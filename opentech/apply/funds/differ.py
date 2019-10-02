import re

from bleach.sanitizer import Cleaner
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
    if should_bleach:
        cleaner = Cleaner(tags=['h4'], attributes={}, strip=True)
        answer_a = re.sub('(<li[^>]*>)', r'\1● ', answer_a)
        answer_b = re.sub('(<li[^>]*>)', r'\1● ', answer_b)
        answer_a = cleaner.clean(answer_a)
        answer_b = cleaner.clean(answer_b)

    diff = SequenceMatcher(None, answer_a, answer_b)
    from_diff = []
    to_diff = []
    for opcode, a0, a1, b0, b1 in diff.get_opcodes():
        if opcode == 'equal':
            from_diff.append(mark_safe(diff.a[a0:a1]))
            to_diff.append(mark_safe(diff.b[b0:b1]))
        elif opcode == 'insert':
            from_diff.append(mark_safe(diff.a[a0:a1]))
            to_diff.append(wrap_with_span(diff.b[b0:b1], 'added'))
        elif opcode == 'delete':
            from_diff.append(wrap_with_span(diff.a[a0:a1], 'deleted'))
            to_diff.append(mark_safe(diff.b[b0:b1]))
        elif opcode == 'replace':
            from_diff.append(wrap_with_span(diff.a[a0:a1], 'deleted'))
            to_diff.append(wrap_with_span(diff.b[b0:b1], 'added'))

    from_display = ''.join(from_diff)
    to_display = ''.join(to_diff)
    from_display = re.sub('([●○]|[0-9]{1,2}[\)\.])', r'<br>\1', from_display)
    to_display = re.sub('([●○]|[0-9]{1,2}[\)\.])', r'<br>\1', to_display)
    from_display = re.sub('(\.\n)', r'\1<br><br>', from_display)
    to_display = re.sub('(\.\n)', r'\1<br><br>', to_display)
    from_display = mark_safe(from_display)
    to_display = mark_safe(to_display)

    return (from_display, to_display)
