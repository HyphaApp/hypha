from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.safestring import mark_safe

from wagtail.wagtailcore import hooks


@hooks.register('insert_editor_js')
def editor_js():
    return mark_safe(
        '<script src="%s"></script>' % static('js/update_person_title.js')
    )
