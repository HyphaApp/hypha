import os

from .base import *  # noqa

# Disable debug mode
DEBUG = False

# Configuration from environment variables
env = os.environ.copy()

# Alternatively, you can set these in a local.py file on the server
try:
     from .local import *  # noqa
except ImportError:
    pass

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
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_sdk.init(
        dsn=env['SENTRY_DSN'],
        environment=env.get('SENTRY_ENVIRONMENT', None),
        integrations=[DjangoIntegration()]
    )

# Heroku configuration.
# Set ON_HEROKU to true in Config Vars or via cli "heroku config:set ON_HEROKU=true".
if 'ON_HEROKU' in env:
    import django_heroku
    django_heroku.settings(locals())
