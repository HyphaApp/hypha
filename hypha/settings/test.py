import logging

from .base import *  # noqa

logging.disable(logging.CRITICAL)


# Should only include explicit testing settings

SECRET_KEY = 'NOT A SECRET'

PROJECTS_ENABLED = True
PROJECTS_AUTO_CREATE = True

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Salesforce Integration
if 'SALESFORCE_INTEGRATION' in env and env['SALESFORCE_INTEGRATION']:
    try:
        from .salesforce import *
    except ImportError:
        pass
    DATABASES.update(SALESFORCE_DB)
