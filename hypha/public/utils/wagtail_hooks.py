from wagtail import hooks
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtailcache.cache import clear_cache

from hypha.public.news.models import NewsType
from hypha.public.people.models import PersonType


class NewsTypeModelAdmin(ModelAdmin):
    model = NewsType
    menu_icon = "tag"


class PersonTypeModelAdmin(ModelAdmin):
    model = PersonType
    menu_icon = "tag"


class TaxonomiesModelAdminGroup(ModelAdminGroup):
    menu_label = "Taxonomies"
    items = (NewsTypeModelAdmin, PersonTypeModelAdmin)
    menu_icon = "tag"


modeladmin_register(TaxonomiesModelAdminGroup)


@hooks.register("after_create_page")
@hooks.register("after_edit_page")
def clear_wagtailcache(request, page):
    if page.live:
        clear_cache()
