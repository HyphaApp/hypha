from django.conf import settings
from wagtail.contrib.modeladmin.options import modeladmin_register
from wagtail.contrib.settings.registry import register_setting

from .admin import ProjectAdminGroup
from .models import ProjectSettings

if settings.PROJECTS_ENABLED:
    modeladmin_register(ProjectAdminGroup)
    register_setting(model=ProjectSettings)
