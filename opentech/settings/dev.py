from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGEME!!!'

INTERNAL_IPS = ('127.0.0.1', '10.0.2.2')

BASE_URL = 'http://localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTH_PASSWORD_VALIDATORS = []

INSTALLED_APPS = INSTALLED_APPS + [
    'wagtail.contrib.wagtailstyleguide',
]

try:
    from .local import *  # noqa
except ImportError:
    pass
