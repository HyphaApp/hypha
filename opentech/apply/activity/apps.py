from django.apps import AppConfig


class ActivityConfig(AppConfig):
    name = 'opentech.apply.activity'

    def ready(self):
        from . import signals
