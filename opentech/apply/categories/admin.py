from wagtail.contrib.modeladmin.options import ModelAdmin

from .models import Category


class CategoryAdmin(ModelAdmin):
    menu_label = 'Category Questions'
    menu_icon = 'list-ul'
    model = Category
