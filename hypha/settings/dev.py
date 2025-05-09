from .base import *  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Automatic reload for development (only when DEBUG is true).
RELOAD = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "CHANGEME!!!"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "hypha.test",
]

RUNSERVERPLUS_SERVER_ADDRESS_PORT = "127.0.0.1:9001"

WAGTAILADMIN_BASE_URL = "http://127.0.0.1:9001"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

AUTH_PASSWORD_VALIDATORS = []

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
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR + "/var/mail"

# Local logging to file.
if LOCAL_FILE_LOGGING:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "null": {
                "level": "DEBUG",
                "class": "logging.NullHandler",
            },
            "logfile": {
                "level": "DEBUG",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": BASE_DIR + "/var/log/debug.log",
                "maxBytes": 1000000,
                "backupCount": 2,
                "formatter": "standard",
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["logfile"],
                "level": "INFO",
                "propagate": True,
            },
            "django.db.backends": {
                "handlers": ["logfile"],
                "level": "INFO",
                "propagate": False,
            },
            "django.request": {
                "handlers": ["logfile"],
                "level": "DEBUG",
                "propagate": False,
            },
            "django.template": {
                "handlers": ["logfile"],
                "level": "INFO",
                "propagate": False,
            },
            "django.security": {
                "handlers": ["logfile"],
                "level": "DEBUG",
                "propagate": False,
            },
            "wagtail": {
                "handlers": ["logfile"],
                "level": "DEBUG",
            },
            "hypha": {
                "handlers": ["logfile"],
                "level": "DEBUG",
            },
            # "werkzeug": {
            #     "handlers": ["console"],
            #     "level": "DEBUG",
            #     "propagate": True,
            # },
        },
    }


# Debug Toolbar
# https://django-debug-toolbar.readthedocs.io/en/latest/index.html
if DEBUG:
    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#configuring-internal-ips
    INTERNAL_IPS = ["127.0.0.1"]

    if RELOAD:
        INSTALLED_APPS = [
            *INSTALLED_APPS,
            "django_browser_reload",
        ]
        MIDDLEWARE = [
            "django_browser_reload.middleware.BrowserReloadMiddleware",
            *MIDDLEWARE,
        ]

# We disable all panels by default here since some of them (SQL, Template,
# Profiling) can be very CPU intensive for this site.  However disabled panels
# can be easily toggled on in the UI.
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": {
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    },
    "SHOW_COLLAPSED": True,
}

SENTRY_DENY_URLS += ["__reload__", "/favicon.ico", "/media/", "/static/", "__debug__"]
