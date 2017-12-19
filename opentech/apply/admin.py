from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .models import Fund


class FundModelAdmin(ModelAdmin):
    model = Fund
    menu_icon = 'site'
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (FundModelAdmin,)
