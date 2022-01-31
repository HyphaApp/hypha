import os

from .base import *  # noqa

# Disable debug mode
DEBUG = False

# Alternatively, you can set these in a local.py file on the server
try:
     from .local import *  # noqa
except ImportError:
    pass

# Mailgun configuration.
if env.str('MAILGUN_API_KEY', None):
    EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
    ANYMAIL = {
        'MAILGUN_API_KEY': env.str('MAILGUN_API_KEY'),
        'MAILGUN_SENDER_DOMAIN': env.str('EMAIL_HOST', None),
        'MAILGUN_API_URL': env.url('MAILGUN_API_URL', 'https://api.mailgun.net/v3'),
        'WEBHOOK_SECRET': env.str('ANYMAIL_WEBHOOK_SECRET', None)
    }

# Sentry configuration.
if env.str('SENTRY_DSN', None):
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=env.str('SENTRY_DSN'),
        environment=env.str('SENTRY_ENVIRONMENT', None),
        integrations=[DjangoIntegration(), CeleryIntegration()]
    )

# Heroku configuration.
# Set ON_HEROKU to true in Config Vars or via cli 'heroku config:set ON_HEROKU=true'.
if env.bool('ON_HEROKU', False):
    import django_heroku
    django_heroku.settings(locals())
