from django.contrib.staticfiles.templatetags.staticfiles import static

from wagtail.contrib.modeladmin.options import ModelAdminGroup, ModelAdmin, modeladmin_register
from wagtail.core import hooks

from wagtailcache.cache import clear_cache

from opentech.public.news.models import NewsType
from opentech.public.people.models import PersonType


class NewsTypeModelAdmin(ModelAdmin):
    model = NewsType
    menu_icon = 'tag'


class PersonTypeModelAdmin(ModelAdmin):
    model = PersonType
    menu_icon = 'tag'


class TaxonomiesModelAdminGroup(ModelAdminGroup):
    menu_label = "Taxonomies"
    items = (NewsTypeModelAdmin, PersonTypeModelAdmin)
    menu_icon = 'tag'


modeladmin_register(TaxonomiesModelAdminGroup)


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
