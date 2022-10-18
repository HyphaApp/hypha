from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ProjectAdminGroup

modeladmin_register(ProjectAdminGroup)
