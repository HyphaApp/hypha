"""
Django settings for opentech project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

import dj_database_url
import raven
from raven.exceptions import InvalidGitRepository


env = os.environ.copy()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

APP_NAME = env.get('APP_NAME', 'opentech')

DEBUG = False


if 'SECRET_KEY' in env:
    SECRET_KEY = env['SECRET_KEY']

if 'ALLOWED_HOSTS' in env:
    ALLOWED_HOSTS = env['ALLOWED_HOSTS'].split(',')


# Email settings
if 'EMAIL_HOST' in env:
    EMAIL_HOST = env['EMAIL_HOST']

if 'EMAIL_PORT' in env:
    try:
        EMAIL_PORT = int(env['EMAIL_PORT'])
    except ValueError:
        pass

if 'EMAIL_HOST_USER' in env:
    EMAIL_HOST_USER = env['EMAIL_HOST_USER']

if 'EMAIL_HOST_PASSWORD' in env:
    EMAIL_HOST_PASSWORD = env['EMAIL_HOST_PASSWORD']

if env.get('EMAIL_USE_TLS', 'false').lower().strip() == 'true':
    EMAIL_USE_TLS = True

if env.get('EMAIL_USE_SSL', 'false').lower().strip() == 'true':
    EMAIL_USE_SSL = True

if 'EMAIL_SUBJECT_PREFIX' in env:
    EMAIL_SUBJECT_PREFIX = env['EMAIL_SUBJECT_PREFIX']

if 'SERVER_EMAIL' in env:
    SERVER_EMAIL = DEFAULT_FROM_EMAIL = env['SERVER_EMAIL']


# Application definition

INSTALLED_APPS = [
    'scout_apm.django',

    'opentech.images',

    'opentech.apply.activity',
    'opentech.apply.categories',
    'opentech.apply.funds',
    'opentech.apply.dashboard',
    'opentech.apply.home',
    'opentech.apply.users',
    'opentech.apply.review',
    'opentech.apply.determinations',
    'opentech.apply.stream_forms',

    'opentech.public.funds',
    'opentech.public.home',
    'opentech.public.mailchimp',
    'opentech.public.navigation',
    'opentech.public.news',
    'opentech.public.people',
    'opentech.public.projects',
    'opentech.public.search',
    'opentech.public.standardpages',
    'opentech.public.utils',

    'social_django',

    'wagtail.contrib.modeladmin',
    'wagtail.contrib.postgres_search',
    'wagtail.contrib.settings',
    'wagtail.contrib.search_promotions',
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail.core',

    'anymail',
    'modelcluster',
    'taggit',
    'django_extensions',
    'tinymce',
    'django_tables2',
    'django_filters',
    'django_select2',
    'addressfield',
    'django_bleach',
    'django_fsm',
    'django_pwned_passwords',

    'hijack',
    'compat',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.forms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_referrer_policy.middleware.ReferrerPolicyMiddleware',

    'opentech.apply.users.middleware.SocialAuthExceptionMiddleware',

    'wagtail.core.middleware.SiteMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',

    'opentech.apply.middleware.apply_url_conf_middleware',
]

ROOT_URLCONF = 'opentech.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_DIR, 'templates'),
            os.path.join(PROJECT_DIR, 'apply', 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'wagtail.contrib.settings.context_processors.settings',
                'opentech.public.utils.context_processors.global_vars',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'opentech.wsgi.application'


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        default=f"postgres:///{APP_NAME}"
    )
}


# Cache
if 'REDIS_URL' in env:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env['REDIS_URL'],
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'database_cache',
        }
    }


# Set s-max-age header that is used by reverse proxy/front end cache. See
# urls.py
try:
    CACHE_CONTROL_S_MAXAGE = int(env.get('CACHE_CONTROL_S_MAXAGE', 600))
except ValueError:
    pass


# Search

WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.contrib.postgres_search.backend',
    },
}


# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django_pwned_passwords.password_validation.PWNEDPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_L10N = False

USE_TZ = True

DATE_FORMAT = 'Y-m-d'

DATETIME_FORMAT = 'Y-m-d\TH:i:s'

SHORT_DATE_FORMAT = 'Y-m-d'

SHORT_DATETIME_FORMAT = 'Y-m-d\TH:i:s'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, 'static_compiled'),
    os.path.join(PROJECT_DIR, '../public'),
]

STATIC_ROOT = env.get('STATIC_DIR', os.path.join(BASE_DIR, 'static'))
STATIC_URL = env.get('STATIC_URL', '/static/')

MEDIA_ROOT = env.get('MEDIA_DIR', os.path.join(BASE_DIR, 'media'))
MEDIA_URL = env.get('MEDIA_URL', '/media/')


AUTH_USER_MODEL = 'users.User'

WAGTAIL_USER_EDIT_FORM = 'opentech.apply.users.forms.CustomUserEditForm'
WAGTAIL_USER_CREATION_FORM = 'opentech.apply.users.forms.CustomUserCreationForm'
WAGTAIL_USER_CUSTOM_FIELDS = ['full_name']

LOGIN_URL = 'users_public:login'
LOGIN_REDIRECT_URL = 'dashboard:dashboard'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        # Send logs with at least INFO level to the console.
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # Send logs with level of at least ERROR to Sentry.
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s'
        }
    },
    'loggers': {
        'opentech': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'sentry'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


# Wagtail settings

WAGTAIL_SITE_NAME = "opentech"

WAGTAILIMAGES_IMAGE_MODEL = "images.CustomImage"
WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = False

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
        # fixed in wagtail 2.0.1: https://github.com/wagtail/wagtail/commit/09f8a4f38a95f2760f38ab2f142443df93b5d8c6
        # 'OPTIONS': {
        #     'features': [
        #         'bold', 'italic',
        #         'h3', 'h4', 'h5',
        #         'ol', 'ul',
        #         'link'
        #     ]
        # }
    },
}


PASSWORD_REQUIRED_TEMPLATE = 'password_required.html'

DEFAULT_PER_PAGE = 20

ESI_ENABLED = False

# Custom settings

ENABLE_STYLEGUIDE = False
DEBUGTOOLBAR = False

# Staff e-mail domain

if 'STAFF_EMAIL_DOMAINS' in env:
    STAFF_EMAIL_DOMAINS = env['STAFF_EMAIL_DOMAINS'].split(',')
else:
    STAFF_EMAIL_DOMAINS = ['opentech.fund']

# Social Auth
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# Set the Google OAuth2 credentials in ENV variables or local.py
# To create a new set of credentials, go to https://console.developers.google.com/apis/credentials
# Make sure the Google+ API is enabled for your API project
if 'SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS' in env:
    SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = env['SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS'].split(',')
else:
    SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = STAFF_EMAIL_DOMAINS

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

SOCIAL_AUTH_LOGIN_ERROR_URL = 'users_public:login'
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = 'users:account'

# For pipelines, see http://python-social-auth.readthedocs.io/en/latest/pipeline.html?highlight=pipelines#authentication-pipeline
# Create / associate accounts (including by email)
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'opentech.apply.users.pipeline.make_otf_staff',
)

# Bleach Settings
BLEACH_ALLOWED_TAGS = ['h2', 'h3', 'p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br']

BLEACH_ALLOWED_ATTRIBUTES = ['href', 'title', 'style']

BLEACH_ALLOWED_STYLES = ['font-family', 'font-weight', 'text-decoration', 'font-variant']

BLEACH_STRIP_TAGS = True

BLEACH_STRIP_COMMENTS = True

# Hijack Settings
HIJACK_LOGIN_REDIRECT_URL = '/dashboard/'
HIJACK_LOGOUT_REDIRECT_URL = '/account/'
HIJACK_DECORATOR = 'opentech.apply.users.decorators.superuser_decorator'


# Messaging Settings
SEND_MESSAGES = env.get('SEND_MESSAGES', 'false').lower() == 'true'
SLACK_DESTINATION_URL = env.get('SLACK_DESTINATION_URL', None)
SLACK_DESTINATION_ROOM = env.get('SLACK_DESTINATION_ROOM', None)


# Celery config
if 'REDIS_URL' in env:
    CELERY_BROKER_URL = env.get('REDIS_URL')
else:
    CELERY_TASK_ALWAYS_EAGER = True


# S3 configuration

if 'AWS_STORAGE_BUCKET_NAME' in env:
    DEFAULT_FILE_STORAGE = 'opentech.storage_backends.PublicMediaStorage'
    PRIVATE_FILE_STORAGE = 'opentech.storage_backends.PrivateMediaStorage'

    AWS_STORAGE_BUCKET_NAME = env['AWS_STORAGE_BUCKET_NAME']

    if 'AWS_PUBLIC_BUCKET_NAME' in env:
        AWS_PUBLIC_BUCKET_NAME = env['AWS_PUBLIC_BUCKET_NAME']
    else:
        AWS_PUBLIC_BUCKET_NAME = env['AWS_STORAGE_BUCKET_NAME']

    if 'AWS_PRIVATE_BUCKET_NAME' in env:
        AWS_PRIVATE_BUCKET_NAME = env['AWS_PRIVATE_BUCKET_NAME']
    else:
        AWS_PRIVATE_BUCKET_NAME = env['AWS_STORAGE_BUCKET_NAME']

    if 'AWS_S3_CUSTOM_DOMAIN' in env:
        AWS_S3_CUSTOM_DOMAIN = env['AWS_S3_CUSTOM_DOMAIN']

    if 'AWS_PRIVATE_CUSTOM_DOMAIN' in env:
        AWS_PRIVATE_CUSTOM_DOMAIN = env['AWS_PRIVATE_CUSTOM_DOMAIN']

    if 'AWS_QUERYSTRING_EXPIRE' in env:
        AWS_QUERYSTRING_EXPIRE = env['AWS_QUERYSTRING_EXPIRE']

    if 'AWS_PUBLIC_CUSTOM_DOMAIN' in env:
        AWS_PUBLIC_CUSTOM_DOMAIN = env['AWS_PUBLIC_CUSTOM_DOMAIN']

    INSTALLED_APPS += (
        'storages',
    )


# Settings to connect to the Bucket from which we are migrating data
AWS_MIGRATION_BUCKET_NAME = env.get('AWS_MIGRATION_BUCKET_NAME', '')
AWS_MIGRATION_ACCESS_KEY_ID = env.get('AWS_MIGRATION_ACCESS_KEY_ID', '')
AWS_MIGRATION_SECRET_ACCESS_KEY = env.get('AWS_MIGRATION_SECRET_ACCESS_KEY', '')


MAILCHIMP_API_KEY = env.get('MAILCHIMP_API_KEY')
MAILCHIMP_LIST_ID = env.get('MAILCHIMP_LIST_ID')


# Raven (sentry) configuration.
if 'SENTRY_DSN' in env:
    INSTALLED_APPS += (
        'raven.contrib.django.raven_compat',
    )

    RAVEN_CONFIG = {
        'dsn': env['SENTRY_DSN'],
        'tags': {},
    }

    # Specifying the programming language as a tag can be useful when
    # e.g. javascript error logging is enabled within the same project,
    # so that errors can be filtered by the programming language too.
    # The 'lang' tag is just an arbitrarily chosen one; any other tags can be used as well.
    # It has to overriden in javascript: Raven.setTagsContext({lang: 'javascript'});
    RAVEN_CONFIG['tags']['lang'] = 'python'

    # Prevent logging errors from the django shell.
    # Errors from other managenent commands will be still logged.
    if len(sys.argv) > 1 and sys.argv[1] in ['shell', 'shell_plus']:
        RAVEN_CONFIG['ignore_exceptions'] = ['*']

    # There's a chooser to toggle between environments at the top right corner on sentry.io
    # Values are typically 'staging' or 'production' but can be set to anything else if needed.
    # heroku config:set SENTRY_ENVIRONMENT=production
    if 'SENTRY_ENVIRONMENT' in env:
        RAVEN_CONFIG['environment'] = env['SENTRY_ENVIRONMENT']

    try:
        RAVEN_CONFIG['release'] = raven.fetch_git_sha(BASE_DIR)
    except InvalidGitRepository:
        try:
            RAVEN_CONFIG['release'] = env['GIT_REV']
        except KeyError:
            pass


# Basic auth settings
if env.get('BASIC_AUTH_ENABLED', 'false').lower().strip() == 'true':
    MIDDLEWARE.insert(0, 'baipw.middleware.BasicAuthIPWhitelistMiddleware')
    BASIC_AUTH_LOGIN = env['BASIC_AUTH_LOGIN']
    BASIC_AUTH_PASSWORD = env['BASIC_AUTH_PASSWORD']
    if 'BASIC_AUTH_WHITELISTED_HTTP_HOSTS' in env:
        BASIC_AUTH_WHITELISTED_HTTP_HOSTS = (
            env['BASIC_AUTH_WHITELISTED_HTTP_HOSTS'].split(',')
        )
    if 'BASIC_AUTH_WHITELISTED_IP_NETWORKS' in env:
        BASIC_AUTH_WHITELISTED_IP_NETWORKS = (
            env['BASIC_AUTH_WHITELISTED_IP_NETWORKS'].split(',')
        )


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


if 'PRIMARY_HOST' in env:
    # This is used by Wagtail's email notifications for constructing absolute
    # URLs.
    BASE_URL = 'https://{}'.format(env['PRIMARY_HOST'])


# Security configuration
# https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security

if env.get('SECURE_SSL_REDIRECT', 'true').strip().lower() == 'true':
    SECURE_SSL_REDIRECT = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if 'SECURE_HSTS_SECONDS' in env:
    try:
        SECURE_HSTS_SECONDS = int(env['SECURE_HSTS_SECONDS'])
    except ValueError:
        pass

if env.get('SECURE_BROWSER_XSS_FILTER', 'true').lower().strip() == 'true':
    SECURE_BROWSER_XSS_FILTER = True

if env.get('SECURE_CONTENT_TYPE_NOSNIFF', 'true').lower().strip() == 'true':
    SECURE_CONTENT_TYPE_NOSNIFF = True


# Referrer-policy header settings
# https://django-referrer-policy.readthedocs.io/en/1.0/

REFERRER_POLICY = env.get('SECURE_REFERRER_POLICY',
                          'no-referrer-when-downgrade').strip()
