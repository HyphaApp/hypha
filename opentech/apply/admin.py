from wagtail.contrib.modeladmin.options import ModelAdmin

from .models import ApplicationForm, Category


class CategoryAdmin(ModelAdmin):
    model = Category


class ApplicationFormAdmin(ModelAdmin):
    model = ApplicationForm
