import logging

logging.disable(logging.CRITICAL)

from .base import *  # noqa

# Should only include explicit testing settings

SECRET_KEY = 'NOT A SECRET'

PROJECTS_ENABLED = True

# Need this to ensure white noise doesn't kill the speed of testing
# http://whitenoise.evans.io/en/latest/django.html#whitenoise-makes-my-tests-run-slow
WHITENOISE_AUTOREFRESH = True
