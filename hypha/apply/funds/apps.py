from django.apps import AppConfig
from django.core.signals import request_finished


class ApplyConfig(AppConfig):
    name = "hypha.apply.funds"

    def ready(self):
        # Connect the attachment deletion handler
        from . import signals

        request_finished.connect(signals.delete_attachments)
