from django.apps import AppConfig


class MessageConfigurationConfig(AppConfig):
    name = "extensions.ots.message_configuration"
    label = "extension_message_configuration"

    def ready(self):
        from . import signals  # noqa

        pass
