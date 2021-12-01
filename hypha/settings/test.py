import logging

from .base import *  # noqa

logging.disable(logging.CRITICAL)


# Should only include explicit testing settings

SECRET_KEY = 'NOT A SECRET'

PROJECTS_ENABLED = True
PROJECTS_AUTO_CREATE = True

TRANSITION_AFTER_REVIEWS = 2
TRANSITION_AFTER_ASSIGNED = True

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
