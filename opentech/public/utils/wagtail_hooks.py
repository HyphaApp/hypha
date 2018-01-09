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
