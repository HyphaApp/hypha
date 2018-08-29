import os
import dj_database_url

from .base import *  # noqa

# Do not set SECRET_KEY, Postgres or LDAP password or any other sensitive data here.
# Instead, use environment variables or create a local.py file on the server.

DEBUG = True


# Cache everything for 10 minutes
# This only applies to pages that do not have a more specific cache-control
# setting. See urls.py
CACHE_CONTROL_MAX_AGE = 600


# Configuration from environment variables
# Alternatively, you can set these in a local.py file on the server

env = os.environ.copy()

# Basic configuration

APP_NAME = env.get('APP_NAME', 'opentech')

SECURE_SSL_REDIRECT = False

if 'DATABASE_URL' in os.environ:
    DATABASES = {'default': dj_database_url.config()}

if 'SECRET_KEY' in env:
    SECRET_KEY = env['SECRET_KEY']

# Email config

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
