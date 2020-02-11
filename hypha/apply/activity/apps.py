from django.apps import AppConfig


class ActivityConfig(AppConfig):
    name = 'hypha.apply.activity'

    def ready(self):
        from . import signals  # NOQA
