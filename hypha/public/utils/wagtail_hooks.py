from django.templatetags.static import static
from wagtail import hooks
from wagtailcache.cache import clear_cache


@hooks.register('insert_editor_css')
def editor_css():
    link = '<link rel="stylesheet" href="{}">\n'
    path = static('css/apply/wagtail_editor.css')
    return link.format(path)


@hooks.register('after_create_page')
@hooks.register('after_edit_page')
def clear_wagtailcache(request, page):
    if page.live:
        clear_cache()
