from difflib import SequenceMatcher
from django_bleach.templatetags.bleach_tags import bleach_value

from django.utils.html import format_html
from django.utils.text import mark_safe


def wrap_with_span(text, class_name):
    return format_html('<span class="diff diff__{}">{}</span>', class_name, mark_safe(text))


def wrap_deleted(text):
    return wrap_with_span(text, 'deleted')


def wrap_added(text):
    return wrap_with_span(text, 'added')


def compare(answer_a, answer_b):
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
    from_display = bleach_value(from_display)
    to_display = bleach_value(to_display)

    return (from_display, to_display)
