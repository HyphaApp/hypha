import django
from celery import Celery
from django.conf import settings

app = Celery("hypha")

# Requires env var `DJANGO_SETTINGS_MODULE` to be set before running

django.setup()

app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks(["django_slack", "hypha.apply.activity"])
