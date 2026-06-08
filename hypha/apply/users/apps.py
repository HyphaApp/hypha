from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "hypha.apply.users"

    def ready(self):
        from . import signals  # NOQA
