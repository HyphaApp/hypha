from django.conf import settings
from wagtail.contrib.modeladmin.options import modeladmin_register

from .admin import ProjectAdminGroup

if settings.PROJECTS_ENABLED:
    modeladmin_register(ProjectAdminGroup)
