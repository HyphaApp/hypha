from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import CategoryAdmin


modeladmin_register(CategoryAdmin)
