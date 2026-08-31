from django.apps import AppConfig


class CoreAppConfig(AppConfig):
    name = "hypha.core"

    def ready(self):
        from hypha.core import checks  # noqa: F401
