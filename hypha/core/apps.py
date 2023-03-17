from django.apps import AppConfig
from django_web_components import component


class CoreAppConfig(AppConfig):
    name = "hypha.core"

    def ready(self):
        from . import components  # noqa
        component.register("adminbar", component=components.AdminBar)

