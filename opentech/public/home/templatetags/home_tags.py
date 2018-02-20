from django import template
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter(name="spanify", is_safe=True)
def spanify(text, num_words):
    parts = text.split()
    parts.insert(num_words, '</span>')
    parts.insert(0, '<span>')
    return mark_safe(' '.join(parts))
