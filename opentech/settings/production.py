import os

import dj_database_url
# import raven
import django_heroku

from .base import *  # noqa

# Do not set SECRET_KEY, Postgres or LDAP password or any other sensitive data here.
# Instead, use environment variables or create a local.py file on the server.

# Disable debug mode
DEBUG = False


# Cache everything for 10 minutes
# This only applies to pages that do not have a more specific cache-control
# setting. See urls.py
CACHE_CONTROL_MAX_AGE = 600


# Configuration from environment variables
# Alternatively, you can set these in a local.py file on the server

env = os.environ.copy()

# Raven (sentry) configuration. See local settings for DSN

if 'SENTRY_DSN' in env:
    INSTALLED_APPS += (
        'raven.contrib.django.raven_compat',
    )

    SENTRY_DSN = env['SENTRY_DSN']


# Basic configuration

APP_NAME = env.get('APP_NAME', 'opentech')

if env.get('SECURE_SSL_REDIRECT', 'true') == 'true':
    SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# enable HSTS only once the site is working properly on https with the actual live domain name
# SECURE_HSTS_SECONDS = 31536000  # 1 year

if 'SECRET_KEY' in env:
    SECRET_KEY = env['SECRET_KEY']

if 'ALLOWED_HOSTS' in env:
    ALLOWED_HOSTS = env['ALLOWED_HOSTS'].split(',')

if 'PRIMARY_HOST' in env:
    BASE_URL = 'https://%s/' % env['PRIMARY_HOST']

if 'STATIC_URL' in env:
    STATIC_URL = env['STATIC_URL']

if 'STATIC_DIR' in env:
    STATIC_ROOT = env['STATIC_DIR']

if 'MEDIA_URL' in env:
    MEDIA_URL = env['MEDIA_URL']

if 'MEDIA_DIR' in env:
    MEDIA_ROOT = env['MEDIA_DIR']

# Email config

if 'SERVER_EMAIL' in env:
    SERVER_EMAIL = env['SERVER_EMAIL']
    DEFAULT_FROM_EMAIL = env['SERVER_EMAIL']

if 'EMAIL_HOST' in env:
    EMAIL_HOST = env['EMAIL_HOST']

if 'MAILGUN_API_KEY' in env:
    EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
    ANYMAIL = {
        "MAILGUN_API_KEY": env['MAILGUN_API_KEY'],
        "MAILGUN_SENDER_DOMAIN": env.get('EMAIL_HOST', None),
        "WEBHOOK_SECRET": env.get('ANYMAIL_WEBHOOK_SECRET', None)
    }

# Social Auth

if 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY' in env:
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env['SOCIAL_AUTH_GOOGLE_OAUTH2_KEY']

if 'SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET' in env:
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env['SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET']

# Basic auth to stop access to other than primary hosts.

MIDDLEWARE += [
    'baipw.middleware.BasicAuthIPWhitelistMiddleware'
]

if 'BASIC_AUTH_LOGIN' in env:
    BASIC_AUTH_LOGIN = env['BASIC_AUTH_LOGIN']

if 'BASIC_AUTH_PASSWORD' in env:
    BASIC_AUTH_PASSWORD = env['BASIC_AUTH_PASSWORD']

if 'BASIC_AUTH_WHITELISTED_HTTP_HOSTS' in env:
    BASIC_AUTH_WHITELISTED_HTTP_HOSTS = env['BASIC_AUTH_WHITELISTED_HTTP_HOSTS'].split(',')

# Cloudflare cache

if 'CLOUDFLARE_API_TOKEN' in env:
    INSTALLED_APPS += ('wagtail.contrib.frontend_cache', )  # noqa
    WAGTAILFRONTENDCACHE = {
        'cloudflare': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
            'EMAIL': env['CLOUDFLARE_API_EMAIL'],
            'TOKEN': env['CLOUDFLARE_API_TOKEN'],
            'ZONEID': env['CLOUDFLARE_API_ZONEID'],
        },
    }


# Database

if 'DATABASE_URL' in os.environ:
    DATABASES = {'default': dj_database_url.config()}

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': env.get('PGDATABASE', APP_NAME),
            # User, host and port can be configured by the PGUSER, PGHOST and
            # PGPORT environment variables (these get picked up by libpq).
        }
    }


# Logging

if 'LOG_DIR' in env:
    # opentech.fund log
    LOGGING['handlers']['opentech_file'] = {
        'level': 'INFO',
        'class': 'cloghandler.ConcurrentRotatingFileHandler',
        'formatter': 'verbose',
        'filename': os.path.join(env['LOG_DIR'], 'opentech.log'),
        'maxBytes': 5242880,  # 5MB
        'backupCount': 5
    }
    LOGGING['loggers']['opentech']['handlers'].append('opentech_file')

    # Wagtail log
    LOGGING['handlers']['wagtail_file'] = {
        'level': 'INFO',
        'class': 'cloghandler.ConcurrentRotatingFileHandler',
        'formatter': 'verbose',
        'filename': os.path.join(env['LOG_DIR'], 'wagtail.log'),
        'maxBytes': 5242880,  # 5MB
        'backupCount': 5
    }
    LOGGING['loggers']['wagtail']['handlers'].append('wagtail_file')

    # Error log
    LOGGING['handlers']['errors_file'] = {
        'level': 'ERROR',
        'class': 'cloghandler.ConcurrentRotatingFileHandler',
        'formatter': 'verbose',
        'filename': os.path.join(env['LOG_DIR'], 'error.log'),
        'maxBytes': 5242880,  # 5MB
        'backupCount': 5
    }
    LOGGING['loggers']['django.request']['handlers'].append('errors_file')
    LOGGING['loggers']['django.security']['handlers'].append('errors_file')

django_heroku.settings(locals())

try:
    from .local import *  # noqa
except ImportError:
    pass
