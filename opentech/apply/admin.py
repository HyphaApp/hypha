from wagtail.contrib.modeladmin.options import ModelAdmin

from .models import Category


class CategoryAdmin(ModelAdmin):
    model = Category
