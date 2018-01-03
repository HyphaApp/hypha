from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ApplicationFormAdmin, CategoryAdmin


modeladmin_register(ApplicationFormAdmin)
modeladmin_register(CategoryAdmin)
