from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGEME!!!'

INTERNAL_IPS = ('127.0.0.1', '10.0.2.2')

ALLOWED_HOSTS = ['apply.localhost', 'localhost', '127.0.0.1', 'apply.lvh.me', 'lvh.me']

BASE_URL = 'http://localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTH_PASSWORD_VALIDATORS = []

INSTALLED_APPS = INSTALLED_APPS + [
    'wagtail.contrib.styleguide',
]

SECURE_SSL_REDIRECT = False

# Change these in local.py.
LOCAL_FILE_LOGGING = False
LOCAL_FILE_EMAIL = False

try:
    from .local import *  # noqa
except ImportError:
    pass

# We add these here so they can react on settings made in local.py.

# E-mail to local files.
if LOCAL_FILE_EMAIL:
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR + '/var/mail'

# Local logging to file.
if LOCAL_FILE_LOGGING:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'standard': {
                'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
                'datefmt': "%Y-%m-%d %H:%M:%S"
            },
        },
        'handlers': {
            'null': {
                'level': 'DEBUG',
                'class': 'logging.NullHandler',
            },
            'logfile': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': BASE_DIR + '/var/log/debug.log',
                'maxBytes': 1000000,
                'backupCount': 2,
                'formatter': 'standard',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['logfile'],
                'level': 'INFO',
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': ['logfile'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['logfile'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'django.template': {
                'handlers': ['logfile'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.security': {
                'handlers': ['logfile'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'wagtail': {
                'handlers': ['logfile'],
                'level': 'DEBUG',
            },
            'opentech': {
                'handlers': ['logfile'],
                'level': 'DEBUG',
            },
        }
    }

# Set up the Django debug toolbar. See also root urls.py.
if DEBUGTOOLBAR:
    INSTALLED_APPS += [
        'debug_toolbar',
    ]

    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE


WEBPACK_LOADER['DEFAULT'].update({
    'STATS_FILE': os.path.join(BASE_DIR, './opentech/static_compiled/app/webpack-stats.json'),
})
