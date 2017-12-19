from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ApplyAdminGroup


modeladmin_register(ApplyAdminGroup)

