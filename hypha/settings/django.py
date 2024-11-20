"""
Django settings for hypha project.
"""

from django.utils.translation import gettext_lazy as _

# Application definition
INSTALLED_APPS = [
    "scout_apm.django",
    "hypha.cookieconsent",
    "hypha.images",
    "hypha.core.apps.CoreAppConfig",
    "hypha.apply.activity",
    "hypha.apply.categories",
    "hypha.apply.funds",
    "hypha.apply.dashboard",
    "hypha.apply.flags",
    "hypha.home",
    "hypha.apply.users",
    "hypha.apply.review",
    "hypha.apply.determinations",
    "hypha.apply.stream_forms",
    "hypha.apply.todo",
    "hypha.apply.translate",
    "hypha.apply.utils.apps.UtilsConfig",
    "hypha.apply.projects.apps.ProjectsConfig",
    "hypha.public.funds",
    "hypha.public.home",
    "hypha.public.navigation",
    "hypha.public.news",
    "hypha.public.people",
    "hypha.public.projects",
    "hypha.public.standardpages",
    "hypha.public.forms",
    "hypha.public.utils",
    "hypha.public.partner",
    "social_django",
    "django_htmx",
    "heroicons",
    "django_web_components",
    "wagtail.contrib.modeladmin",
    "wagtail.contrib.settings",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "anymail",
    "modelcluster",
    "taggit",
    "django_extensions",
    "tinymce",
    "django_tables2",
    "django_filters",
    "django_select2",
    "hypha.addressfield",
    "django_nh3",
    "django_fsm",
    "django_slack",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "two_factor",
    "rest_framework",
    "rest_framework_api_key",
    "django_file_form",
    "rolepermissions",
    "hijack",
    "elevate",  # https://django-elevate.readthedocs.io/
    "pagedown",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.forms",
    "formtools",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "elevate.middleware.ElevateMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_referrer_policy.middleware.ReferrerPolicyMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "hypha.apply.users.middleware.TwoFactorAuthenticationMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "hypha.apply.users.middleware.SocialAuthExceptionMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
    "hypha.apply.middleware.HandleProtectionErrorMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "hypha.core.middleware.htmx.HtmxMessageMiddleware",
]

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        # Send logs with at least INFO level to the console.
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s"
        }
    },
    "loggers": {
        "hypha": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "wagtail": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "pwned_passwords_django.validators.PwnedPasswordsValidator",
        "OPTIONS": {
            "error_message": _(
                "This password has previously appeared in a data breach and should not be used. Please choose a different password."
            ),
            "help_message": _(
                "Your password must not have been detected in a major security breach."
            ),
        },
    },
]

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = False
USE_TZ = True
DATE_FORMAT = "N j, Y"
DATETIME_FORMAT = "N j, Y, H:i"
SHORT_DATE_FORMAT = "Y-m-d"
SHORT_DATETIME_FORMAT = "Y-m-d H:i"

DATETIME_INPUT_FORMATS = [
    "%Y-%m-%d %H:%M:%S",  # '2006-10-25 14:30:59'
    "%Y-%m-%d %H:%M:%S.%f",  # '2006-10-25 14:30:59.000200'
    "%Y-%m-%d %H:%M",  # '2006-10-25 14:30'
    "%Y-%m-%dT%H:%M",  # '2006-10-25T14:30 (this is extra)'
    "%Y-%m-%d",  # '2006-10-25'
    "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
    "%m/%d/%Y %H:%M:%S.%f",  # '10/25/2006 14:30:59.000200'
    "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
    "%m/%d/%Y",  # '10/25/2006'
    "%m/%d/%y %H:%M:%S",  # '10/25/06 14:30:59'
    "%m/%d/%y %H:%M:%S.%f",  # '10/25/06 14:30:59.000200'
    "%m/%d/%y %H:%M",  # '10/25/06 14:30'
    "%m/%d/%y",  # '10/25/06'
]

AUTH_USER_MODEL = "users.User"

LOGIN_URL = "users:passwordless_login_signup"
LOGIN_REDIRECT_URL = "dashboard:dashboard"

# https://django-elevate.readthedocs.io/en/latest/config/index.html#configuration
ELEVATE_URL = "users:elevate"
ELEVATE_REDIRECT_URL = LOGIN_REDIRECT_URL

CUSTOM_AUTH_BACKEND = "hypha.apply.users.backends.CustomModelBackend"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    CUSTOM_AUTH_BACKEND,
)

# django-rolepermissions
# https://django-role-permissions.readthedocs.io/en/stable/settings.html
ROLEPERMISSIONS_MODULE = "hypha.apply.users.roles"

# Default Auto field configuration
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# The full Python import path to your root URLconf.
ROOT_URLCONF = "hypha.urls"

# The class that renders form widgets
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Python path of the WSGI application object
WSGI_APPLICATION = "hypha.wsgi.application"
