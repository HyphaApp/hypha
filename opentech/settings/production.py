import os

import django_heroku

from .base import *  # noqa

# Disable debug mode
DEBUG = False

# Configuration from environment variables
# Alternatively, you can set these in a local.py file on the server

env = os.environ.copy()
# Basic configuration

if 'MAILGUN_API_KEY' in env:
    EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
    ANYMAIL = {
        "MAILGUN_API_KEY": env['MAILGUN_API_KEY'],
        "MAILGUN_SENDER_DOMAIN": env.get('EMAIL_HOST', None),
        "WEBHOOK_SECRET": env.get('ANYMAIL_WEBHOOK_SECRET', None)
    }

WEBPACK_LOADER['DEFAULT'].update({
    'STATS_FILE': os.path.join(BASE_DIR, './opentech/static_compiled/app/webpack-stats-prod.json'),
})

django_heroku.settings(locals())
