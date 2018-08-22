from wagtail.core import hooks
from wagtail.contrib.modeladmin.options import ModelAdminGroup, ModelAdmin, modeladmin_register

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


# Hide forms from the side menu, remove if adding public.forms back in
@hooks.register('construct_main_menu')
def hide_snippets_menu_item(request, menu_items):
    menu_items[:] = [item for item in menu_items if item.name != 'forms']
