"""
elevate.apps
~~~~~~~~~~~~~~

:copyright: (c) 2017-present by Justin Mayer.
:license: BSD, see LICENSE for more details.
"""

from django.apps import AppConfig


class ElevateConfig(AppConfig):
    name = "elevate"
    verbose_name = "Django Elevate"

    def ready(self):
        # register signals
        import elevate.signals  # noqa
