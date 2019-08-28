import os

import django_heroku
import sentry_sdk

from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa

# Disable debug mode
DEBUG = False

# Configuration from environment variables
# Alternatively, you can set these in a local.py file on the server

env = os.environ.copy()

# Mailgun configuration.
if 'MAILGUN_API_KEY' in env:
    EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
    ANYMAIL = {
        "MAILGUN_API_KEY": env['MAILGUN_API_KEY'],
        "MAILGUN_SENDER_DOMAIN": env.get('EMAIL_HOST', None),
        "WEBHOOK_SECRET": env.get('ANYMAIL_WEBHOOK_SECRET', None)
    }

# Sentry configuration.
if 'SENTRY_DSN' in env:
    sentry_sdk.init(
        dsn=env['SENTRY_DSN'],
        environment=env.get('SENTRY_ENVIRONMENT', None),
        integrations=[DjangoIntegration()]
    )

# Heroku configuration.
django_heroku.settings(locals())
