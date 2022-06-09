"""
Django settings for hypha project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import dj_database_url
from environs import Env

env = Env()
env.read_env()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

APP_NAME = env.str('APP_NAME', 'hypha')

DEBUG = False

# SECRET_KEY is required
SECRET_KEY = env.str('SECRET_KEY', None)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', [])


# Organisation name and e-mail address, used in e-mail templates etc.
ORG_LONG_NAME = env.str('ORG_LONG_NAME', 'Acme Corporation')
ORG_SHORT_NAME = env.str('ORG_SHORT_NAME', 'ACME')
ORG_EMAIL = env.str('ORG_EMAIL', 'info@example.org')
ORG_GUIDE_URL = env.str('ORG_GUIDE_URL', 'https://guide.example.org/')


# Email settings
EMAIL_HOST = env.str('EMAIL_HOST', None)
EMAIL_PORT = env.int('EMAIL_PORT', None)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', None)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', False)
EMAIL_SUBJECT_PREFIX = env.str('EMAIL_SUBJECT_PREFIX', None)
SERVER_EMAIL = DEFAULT_FROM_EMAIL = env.str('SERVER_EMAIL', None)


# Application definition
INSTALLED_APPS = [
    'scout_apm.django',

    'hypha.cookieconsent',
    'hypha.images',

    'hypha.apply.activity',
    'hypha.apply.categories',
    'hypha.apply.funds',
    'hypha.apply.dashboard',
    'hypha.apply.flags',
    'hypha.apply.home',
    'hypha.apply.users',
    'hypha.apply.review',
    'hypha.apply.determinations',
    'hypha.apply.stream_forms',
    'hypha.apply.utils',
    'hypha.apply.projects.apps.ProjectsConfig',

    'hypha.public.funds',
    'hypha.public.home',
    'hypha.public.mailchimp',
    'hypha.public.navigation',
    'hypha.public.news',
    'hypha.public.people',
    'hypha.public.projects',
    'hypha.public.search',
    'hypha.public.standardpages',
    'hypha.public.forms',
    'hypha.public.utils',
    'hypha.public.partner',

    'social_django',

    'wagtail.contrib.modeladmin',
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
    'django_slack',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'two_factor',
    'drf_yasg',
    'rest_framework',
    'rest_framework_api_key',
    'wagtailcache',
    'wagtail_purge',
    'django_file_form',

    'hijack',
    'pagedown',
    'salesforce',

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
    'formtools',
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
    'django_otp.middleware.OTPMiddleware',
    'hypha.apply.users.middleware.TwoFactorAuthenticationMiddleware',

    'hijack.middleware.HijackUserMiddleware',

    'hypha.apply.users.middleware.SocialAuthExceptionMiddleware',

    'wagtail.contrib.redirects.middleware.RedirectMiddleware',

    'hypha.apply.middleware.apply_url_conf_middleware',
    'hypha.apply.middleware.HandleProtectionErrorMiddleware',
]

ROOT_URLCONF = 'hypha.urls'

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
                'hypha.public.utils.context_processors.global_vars',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'hypha.apply.projects.context_processors.projects_enabled',
                'hypha.cookieconsent.context_processors.cookies_accepted',
            ],
        },
    },
]

FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

WSGI_APPLICATION = 'hypha.wsgi.application'

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        default=f'postgres:///{APP_NAME}'
    )
}

# Cache

# Set max-age header.
CACHE_CONTROL_MAX_AGE = env.int('CACHE_CONTROL_MAX_AGE', 3600)

# Set s-max-age header that is used by reverse proxy/front end cache.
CACHE_CONTROL_S_MAXAGE = env.int('CACHE_CONTROL_S_MAXAGE', 3600)

# Set wagtail cache timeout (automatic cache refresh).
WAGTAIL_CACHE_TIMEOUT = CACHE_CONTROL_MAX_AGE

# Set feed cache timeout (automatic cache refresh).
FEED_CACHE_TIMEOUT = 600

# Set X-Frame-Options header for every outgoing HttpResponse
X_FRAME_OPTIONS = 'SAMEORIGIN'

if env.str('REDIS_URL', None):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env.dj_cache_url('REDIS_URL'),
        },
        'wagtailcache': {
            'BACKEND': 'wagtailcache.compat_backends.django_redis.RedisCache',
            'LOCATION': env.dj_cache_url('REDIS_URL'),
            'KEY_PREFIX': 'wagtailcache',
            'TIMEOUT': WAGTAIL_CACHE_TIMEOUT,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'database_cache',
        },
        'wagtailcache': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'database_cache',
            'KEY_PREFIX': 'wagtailcache',
            'TIMEOUT': WAGTAIL_CACHE_TIMEOUT,
        }
    }

# Use a more permanent cache for django-file-form.
# It uses it to store metadata about files while they are being uploaded.
# This might reduce the likelihood of any interruptions on heroku.
# NB It doesn't matter what the `KEY_PREFIX` is,
# `clear_cache` will clear all caches with the same `LOCATION`.
CACHES['django_file_form'] = {
    'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    'LOCATION': 'database_cache',
    'KEY_PREFIX': 'django_file_form',
}

WAGTAIL_CACHE_BACKEND = 'wagtailcache'

# Cloudflare cache invalidation.
# See https://docs.wagtail.io/en/v2.8/reference/contrib/frontendcache.html
if env.str('CLOUDFLARE_BEARER_TOKEN', None) and env.str('CLOUDFLARE_API_ZONEID'):
    INSTALLED_APPS += ('wagtail.contrib.frontend_cache', )  # noqa
    WAGTAILFRONTENDCACHE = {
        'cloudflare': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
            'BEARER_TOKEN': env.str('CLOUDFLARE_BEARER_TOKEN'),
            'ZONEID': env.str('CLOUDFLARE_API_ZONEID'),
        },
    }


# Search
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
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

# Number of seconds that password reset and account activation links are valid (default 259200, 3 days).
PASSWORD_RESET_TIMEOUT = env.int('PASSWORD_RESET_TIMEOUT', 259200)

# Seconds to enter password on password page while email change/2FA change (default 120).
PASSWORD_PAGE_TIMEOUT = env.int('PASSWORD_PAGE_TIMEOUT', 120)

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

# Language code in standard language id format: en, en-gb, en-us
# The corrosponding locale dir is named: en, en_GB, en_US
LANGUAGE_CODE = env.str('LANGUAGE_CODE', 'en')

CURRENCY_SYMBOL = env.str('CURRENCY_SYMBOL', '$')

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = False
USE_TZ = True
DATE_FORMAT = 'N j, Y'
DATETIME_FORMAT = 'N j, Y, H:i'
SHORT_DATE_FORMAT = 'Y-m-d'
SHORT_DATETIME_FORMAT = 'Y-m-d H:i'

DATETIME_INPUT_FORMATS = [
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M:%S.%f',  # '2006-10-25 14:30:59.000200'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%dT%H:%M',        # '2006-10-25T14:30 (this is extra)'
    '%Y-%m-%d',              # '2006-10-25'
    '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    '%m/%d/%Y %H:%M:%S.%f',  # '10/25/2006 14:30:59.000200'
    '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    '%m/%d/%Y',              # '10/25/2006'
    '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    '%m/%d/%y %H:%M:%S.%f',  # '10/25/06 14:30:59.000200'
    '%m/%d/%y %H:%M',        # '10/25/06 14:30'
    '%m/%d/%y',              # '10/25/06'
]

LOCALE_PATHS = (
    PROJECT_DIR + '/locale',
)

# Default Auto field configuration
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, 'static_compiled'),
    os.path.join(PROJECT_DIR, '../public'),
]

STATIC_ROOT = env.str('STATIC_DIR', os.path.join(BASE_DIR, 'static'))
STATIC_URL = env.str('STATIC_URL', '/static/')

MEDIA_ROOT = env.str('MEDIA_DIR', os.path.join(BASE_DIR, 'media'))
MEDIA_URL = env.str('MEDIA_URL', '/media/')

AUTH_USER_MODEL = 'users.User'

WAGTAIL_USER_EDIT_FORM = 'hypha.apply.users.forms.CustomUserEditForm'
WAGTAIL_USER_CREATION_FORM = 'hypha.apply.users.forms.CustomUserCreationForm'
WAGTAIL_USER_CUSTOM_FIELDS = ['full_name']
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False
WAGTAILUSERS_PASSWORD_ENABLED = False
WAGTAILUSERS_PASSWORD_REQUIRED = False

# Enforce Two factor setting
ENFORCE_TWO_FACTOR = env.bool('ENFORCE_TWO_FACTOR', False)

# Give staff lead permissions.
# Only effects setting external reviewers for now.
GIVE_STAFF_LEAD_PERMS = env.bool('GIVE_STAFF_LEAD_PERMS', False)


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
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s][%(process)d][%(levelname)s][%(name)s] %(message)s'
        }
    },
    'loggers': {
        'hypha': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}


# Wagtail settings
WAGTAIL_FRONTEND_LOGIN_URL = '/login/'
WAGTAIL_SITE_NAME = 'hypha'
WAGTAILIMAGES_IMAGE_MODEL = 'images.CustomImage'
WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = False

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
        'OPTIONS': {
            'features': [
                'bold', 'italic',
                'h1', 'h2', 'h3', 'h4', 'h5',
                'ol', 'ul',
                'link'
            ]
        }
    },
}

WAGTAILEMBEDS_RESPONSIVE_HTML = True

PASSWORD_REQUIRED_TEMPLATE = 'password_required.html'

DEFAULT_PER_PAGE = 20

ESI_ENABLED = False

ENABLE_STYLEGUIDE = False
DEBUGTOOLBAR = False

# Staff e-mail domain
STAFF_EMAIL_DOMAINS = env.list('STAFF_EMAIL_DOMAINS', [])

# Social Auth
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# Set the Google OAuth2 credentials in ENV variables or local.py
# To create a new set of credentials, go to https://console.developers.google.com/apis/credentials
# Make sure the Google+ API is enabled for your API project
SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = env.list('SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS', STAFF_EMAIL_DOMAINS)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.str('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.str('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

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
    'hypha.apply.users.pipeline.make_otf_staff',
)

# Bleach Settings
BLEACH_ALLOWED_TAGS = ['a', 'b', 'big', 'blockquote', 'br', 'cite', 'code', 'col', 'colgroup', 'dd', 'del', 'dl', 'dt', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'ins', 'li', 'ol', 'p', 'pre', 'small', 'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul']
BLEACH_ALLOWED_ATTRIBUTES = ['class', 'colspan', 'href', 'rowspan', 'target', 'title', 'width']
BLEACH_ALLOWED_STYLES = []
BLEACH_STRIP_TAGS = True
BLEACH_STRIP_COMMENTS = True

# File Field settings
FILE_ALLOWED_EXTENSIONS = ['doc', 'docx', 'odp', 'ods', 'odt', 'pdf', 'ppt', 'pptx', 'rtf', 'txt', 'xls', 'xlsx']

# Accept attribute in input tag of type file needs filename extensions, starting with a period ('.') character.
FILE_ACCEPT_ATTR_VALUE = ', '.join(['.' + ext for ext in FILE_ALLOWED_EXTENSIONS])

# Hijack Settings
HIJACK_ENABLE = env.bool('HIJACK_ENABLE', False)
HIJACK_LOGIN_REDIRECT_URL = '/dashboard/'
HIJACK_LOGOUT_REDIRECT_URL = '/account/'
HIJACK_DECORATOR = 'hypha.apply.users.decorators.superuser_decorator'
HIJACK_PERMISSION_CHECK = 'hijack.permissions.superusers_and_staff'


# Messaging Settings
SEND_MESSAGES = env.bool('SEND_MESSAGES', False)

if not SEND_MESSAGES:
    from django.contrib.messages import constants as message_constants
    MESSAGE_LEVEL = message_constants.DEBUG


SEND_READY_FOR_REVIEW = env.bool('SEND_READY_FOR_REVIEW', True)

SLACK_DESTINATION_URL = env.str('SLACK_DESTINATION_URL', None)
SLACK_DESTINATION_ROOM = env.str('SLACK_DESTINATION_ROOM', None)
SLACK_DESTINATION_ROOM_COMMENTS = env.str('SLACK_DESTINATION_ROOM_COMMENTS', None)
SLACK_TYPE_COMMENTS = env.list('SLACK_TYPE_COMMENTS', [])

# Django Slack settings
SLACK_TOKEN = env.str('SLACK_TOKEN', None)
SLACK_BACKEND = 'django_slack.backends.CeleryBackend'  # UrllibBackend can be used for async
if SLACK_DESTINATION_URL:
    SLACK_ENDPOINT_URL = SLACK_DESTINATION_URL

# Automatic transition settings
TRANSITION_AFTER_REVIEWS = env.bool('TRANSITION_AFTER_REVIEWS', False)
TRANSITION_AFTER_ASSIGNED = env.bool('TRANSITION_AFTER_ASSIGNED', False)


# Exclude Filters/columns from submission tables.
# Possible values are: fund, round, status, lead, reviewers, screening_statuses, category_options, meta_terms
SUBMISSIONS_TABLE_EXCLUDED_FIELDS = env.list('SUBMISSIONS_TABLE_EXCLUDED_FIELDS', [])

# Celery config
if env.str('REDIS_URL', None):
    CELERY_BROKER_URL = env.str('REDIS_URL')
else:
    CELERY_TASK_ALWAYS_EAGER = True


# S3 configuration
if env.str('AWS_STORAGE_BUCKET_NAME', None):
    DEFAULT_FILE_STORAGE = 'hypha.storage_backends.PublicMediaStorage'
    PRIVATE_FILE_STORAGE = 'hypha.storage_backends.PrivateMediaStorage'
    AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME')
    AWS_PUBLIC_BUCKET_NAME = env.str('AWS_PUBLIC_BUCKET_NAME', AWS_STORAGE_BUCKET_NAME)
    AWS_PRIVATE_BUCKET_NAME = env.str('AWS_PRIVATE_BUCKET_NAME', AWS_STORAGE_BUCKET_NAME)
    AWS_S3_CUSTOM_DOMAIN = env.str('AWS_S3_CUSTOM_DOMAIN', None)
    AWS_PRIVATE_CUSTOM_DOMAIN = env.str('AWS_PRIVATE_CUSTOM_DOMAIN', None)
    AWS_QUERYSTRING_EXPIRE = env.str('AWS_QUERYSTRING_EXPIRE', None)
    AWS_PUBLIC_CUSTOM_DOMAIN = env.str('AWS_PUBLIC_CUSTOM_DOMAIN', None)
    INSTALLED_APPS += (
        'storages',
    )

# Settings to connect to the Bucket from which we are migrating data
AWS_MIGRATION_BUCKET_NAME = env.str('AWS_MIGRATION_BUCKET_NAME', '')
AWS_MIGRATION_ACCESS_KEY_ID = env.str('AWS_MIGRATION_ACCESS_KEY_ID', '')
AWS_MIGRATION_SECRET_ACCESS_KEY = env.str('AWS_MIGRATION_SECRET_ACCESS_KEY', '')

# Mailchimp settings.
MAILCHIMP_API_KEY = env.str('MAILCHIMP_API_KEY', None)
MAILCHIMP_LIST_ID = env.str('MAILCHIMP_LIST_ID', None)


# Basic auth settings
if env.bool('BASIC_AUTH_ENABLED', False):
    MIDDLEWARE.insert(0, 'baipw.middleware.BasicAuthIPWhitelistMiddleware')
    BASIC_AUTH_LOGIN = env.str('BASIC_AUTH_LOGIN', None)
    BASIC_AUTH_PASSWORD = env.str('BASIC_AUTH_PASSWORD', None)
    BASIC_AUTH_WHITELISTED_HTTP_HOSTS = env.list('BASIC_AUTH_WHITELISTED_HTTP_HOSTS', [])
    BASIC_AUTH_WHITELISTED_IP_NETWORKS = env.list('BASIC_AUTH_WHITELISTED_IP_NETWORKS', [])


if env.str('PRIMARY_HOST', None):
    # This is used by Wagtail's email notifications for constructing absolute
    # URLs.
    BASE_URL = 'https://{}'.format(env.str('PRIMARY_HOST'))


# Security configuration
# https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', True)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', None)
SECURE_BROWSER_XSS_FILTER = env.bool('SECURE_BROWSER_XSS_FILTER', True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', True)

if env.bool('COOKIE_SECURE', False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# Referrer-policy header settings
# https://django-referrer-policy.readthedocs.io/en/1.0/

REFERRER_POLICY = env.str('SECURE_REFERRER_POLICY',
                          'no-referrer-when-downgrade').strip()

# Webpack bundle loader
# When disabled, all included bundles are silently ignored.
ENABLE_WEBPACK_BUNDLES = env.bool('ENABLE_WEBPACK_BUNDLES', True)

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'app/',
        'STATS_FILE': os.path.join(BASE_DIR, './hypha/static_compiled/app/webpack-stats-prod.json'),
    }
}

# Django countries package provides ISO 3166-1 countries which does not contain Kosovo.
COUNTRIES_OVERRIDE = {
    'KV': 'Kosovo',
}

# Rest Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}


# Projects Feature Flag
PROJECTS_ENABLED = env.bool('PROJECTS_ENABLED', False)

PROJECTS_AUTO_CREATE = env.bool('PROJECTS_AUTO_CREATE', False)

# Salesforce integration
if env.bool('SALESFORCE_INTEGRATION', False):
    DATABASES = {
        **DATABASES,
        'salesforce': {
            'ENGINE': 'salesforce.backend',
            'CONSUMER_KEY': env.str('SALESFORCE_CONSUMER_KEY', ''),
            'CONSUMER_SECRET': env.str('SALESFORCE_CONSUMER_SECRET', ''),
            'USER': env.str('SALESFORCE_USER', ''),
            'PASSWORD': env.str('SALESFORCE_PASSWORD', ''),
            'HOST': env.str('SALESFORCE_LOGIN_URL', '')
        }
    }

    SALESFORCE_QUERY_TIMEOUT = (30, 30)  # (connect timeout, data timeout)

    DATABASE_ROUTERS = [
        'salesforce.router.ModelRouter'
    ]


# django-file-form settings
FILE_FORM_CACHE = 'django_file_form'
FILE_FORM_UPLOAD_DIR = 'temp_uploads'
# Ensure FILE_FORM_UPLOAD_DIR exists:
os.makedirs(os.path.join(MEDIA_ROOT, FILE_FORM_UPLOAD_DIR), exist_ok=True)
# Store temporary files on S3 too (files are still uploaded to local filesystem first)
if env.str('AWS_STORAGE_BUCKET_NAME', None):
    FILE_FORM_TEMP_STORAGE = PRIVATE_FILE_STORAGE

# Matomo tracking
MATOMO_URL = env.str('MATOMO_URL', None)
MATOMO_SITEID = env.str('MATOMO_SITEID', None)

# Sage IntAcct integration
INTACCT_ENABLED = env.bool('INTACCT_ENABLED', False)
INTACCT_SENDER_ID = env.str('INTACCT_SENDER_ID', '')
INTACCT_SENDER_PASSWORD = env.str('INTACCT_SENDER_PASSWORD', '')
INTACCT_USER_ID = env.str('INTACCT_USER_ID', '')
INTACCT_COMPANY_ID = env.str('INTACCT_COMPANY_ID', '')
INTACCT_USER_PASSWORD = env.str('INTACCT_USER_PASSWORD', '')
