import logging

from .base import *  # noqa

logging.disable(logging.CRITICAL)


# Should only include explicit testing settings

SECRET_KEY = "NOT A SECRET"

HIJACK_ENABLE = True

PROJECTS_ENABLED = True
PROJECTS_AUTO_CREATE = True

TRANSITION_AFTER_REVIEWS = 2
TRANSITION_AFTER_ASSIGNED = True

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

WAGTAILADMIN_BASE_URL = "https://primary-test-host.org"

# Required by django-coverage-plugin to report template coverage
TEMPLATES[0]["OPTIONS"]["debug"] = True

# An extra salt to be added into the cookie signature.
ELEVATE_COOKIE_SALT = SECRET_KEY

ENFORCE_TWO_FACTOR = False

SECURE_SSL_REDIRECT = False
