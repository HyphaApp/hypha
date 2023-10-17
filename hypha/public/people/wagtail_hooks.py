from django.templatetags.static import static
from django.utils.safestring import mark_safe
from wagtail import hooks


@hooks.register("insert_editor_js")
def editor_js():
    return mark_safe(
        '<script src="%s"></script>' % static("people/admin/js/update_person_title.js")
    )
