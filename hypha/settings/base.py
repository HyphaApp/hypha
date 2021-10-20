"""
Django settings for hypha project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

import dj_database_url

env = os.environ.copy()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

APP_NAME = env.get('APP_NAME', 'hypha')

DEBUG = False


if 'SECRET_KEY' in env:
    SECRET_KEY = env['SECRET_KEY']

if 'ALLOWED_HOSTS' in env:
    ALLOWED_HOSTS = env['ALLOWED_HOSTS'].split(',')


# Organisation name and e-mail address, used in e-mail templates etc.

ORG_LONG_NAME = env.get('ORG_LONG_NAME', 'Acme Corporation')
ORG_SHORT_NAME = env.get('ORG_SHORT_NAME', 'ACME')
ORG_EMAIL = env.get('ORG_EMAIL', 'info@example.org')
ORG_GUIDE_URL = env.get('ORG_GUIDE_URL', 'https://guide.example.org/')


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
        default=f"postgres:///{APP_NAME}"
    )
}


# Cache

# Set max-age header.
try:
    CACHE_CONTROL_MAX_AGE = int(env.get('CACHE_CONTROL_MAX_AGE', 3600))
except ValueError:
    CACHE_CONTROL_MAX_AGE = 3600

# Set s-max-age header that is used by reverse proxy/front end cache.
try:
    CACHE_CONTROL_S_MAXAGE = int(env.get('CACHE_CONTROL_S_MAXAGE', 3600))
except ValueError:
    CACHE_CONTROL_S_MAXAGE = 3600

# Set wagtail cache timeout (automatic cache refresh).
WAGTAIL_CACHE_TIMEOUT = CACHE_CONTROL_MAX_AGE

# Set feed cache timeout (automatic cache refresh).
FEED_CACHE_TIMEOUT = 600

if 'REDIS_URL' in env:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': env['REDIS_URL'],
        },
        'wagtailcache': {
            'BACKEND': 'wagtailcache.compat_backends.django_redis.RedisCache',
            'LOCATION': env['REDIS_URL'],
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
if 'CLOUDFLARE_BEARER_TOKEN' in env and 'CLOUDFLARE_API_ZONEID' in env:
    INSTALLED_APPS += ('wagtail.contrib.frontend_cache', )  # noqa
    WAGTAILFRONTENDCACHE = {
        'cloudflare': {
            'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
            'BEARER_TOKEN': env['CLOUDFLARE_BEARER_TOKEN'],
            'ZONEID': env['CLOUDFLARE_API_ZONEID'],
        },
    }


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

# Number of days that password reset and account activation links are valid (default 3).
if 'PASSWORD_RESET_TIMEOUT_DAYS' in env:
    try:
        PASSWORD_RESET_TIMEOUT_DAYS = int(env['PASSWORD_RESET_TIMEOUT_DAYS'])
    except ValueError:
        pass

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

# Language code in standard language id format: en, en-gb, en-us
# The corrosponding locale dir is named: en, en_GB, en_US
LANGUAGE_CODE = env.get('LANGUAGE_CODE', 'en')

CURRENCY_SYMBOL = env.get('CURRENCY_SYMBOL', '$')

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

WAGTAIL_USER_EDIT_FORM = 'hypha.apply.users.forms.CustomUserEditForm'
WAGTAIL_USER_CREATION_FORM = 'hypha.apply.users.forms.CustomUserCreationForm'
WAGTAIL_USER_CUSTOM_FIELDS = ['full_name']
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False
WAGTAILUSERS_PASSWORD_ENABLED = False
WAGTAILUSERS_PASSWORD_REQUIRED = False

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

# Custom settings

ENABLE_STYLEGUIDE = False
DEBUGTOOLBAR = False

# Staff e-mail domain

if 'STAFF_EMAIL_DOMAINS' in env:
    STAFF_EMAIL_DOMAINS = env['STAFF_EMAIL_DOMAINS'].split(',')
else:
    STAFF_EMAIL_DOMAINS = []

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
HIJACK_LOGIN_REDIRECT_URL = '/dashboard/'
HIJACK_LOGOUT_REDIRECT_URL = '/account/'
HIJACK_DECORATOR = 'hypha.apply.users.decorators.superuser_decorator'


# Messaging Settings
SEND_MESSAGES = env.get('SEND_MESSAGES', 'false').lower() == 'true'

if not SEND_MESSAGES:
    from django.contrib.messages import constants as message_constants
    MESSAGE_LEVEL = message_constants.DEBUG


SEND_READY_FOR_REVIEW = env.get('SEND_READY_FOR_REVIEW', 'true').lower() == 'true'

SLACK_DESTINATION_URL = env.get('SLACK_DESTINATION_URL', None)
SLACK_DESTINATION_ROOM = env.get('SLACK_DESTINATION_ROOM', None)
SLACK_DESTINATION_ROOM_COMMENTS = env.get('SLACK_DESTINATION_ROOM_COMMENTS', None)
if 'SLACK_TYPE_COMMENTS' in env:
    SLACK_TYPE_COMMENTS = env['SLACK_TYPE_COMMENTS'].split(',')
else:
    SLACK_TYPE_COMMENTS = []


# Automatic transition settings
TRANSITION_AFTER_REVIEWS = False
if 'TRANSITION_AFTER_REVIEWS' in env:
    try:
        TRANSITION_AFTER_REVIEWS = int(env['TRANSITION_AFTER_REVIEWS'])
    except ValueError:
        pass


# Exclude Filters/columns from submission tables.
# Possible values are: fund, round, status, lead, reviewers, screening_statuses, category_options, meta_terms
if 'SUBMISSIONS_TABLE_EXCLUDED_FIELDS' in env:
    SUBMISSIONS_TABLE_EXCLUDED_FIELDS = env['SUBMISSIONS_TABLE_EXCLUDED_FIELDS'].split(',')
else:
    SUBMISSIONS_TABLE_EXCLUDED_FIELDS = []

# Celery config
if 'REDIS_URL' in env:
    CELERY_BROKER_URL = env.get('REDIS_URL')
else:
    CELERY_TASK_ALWAYS_EAGER = True


# S3 configuration

if 'AWS_STORAGE_BUCKET_NAME' in env:
    DEFAULT_FILE_STORAGE = 'hypha.storage_backends.PublicMediaStorage'
    PRIVATE_FILE_STORAGE = 'hypha.storage_backends.PrivateMediaStorage'

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

if env.get('COOKIE_SECURE', 'false').lower().strip() == 'true':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# Referrer-policy header settings
# https://django-referrer-policy.readthedocs.io/en/1.0/

REFERRER_POLICY = env.get('SECURE_REFERRER_POLICY',
                          'no-referrer-when-downgrade').strip()

# Webpack bundle loader
# When disabled, all included bundles are silently ignored.
if env.get('ENABLE_WEBPACK_BUNDLES', 'true').lower().strip() == 'true':
    ENABLE_WEBPACK_BUNDLES = True

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
PROJECTS_ENABLED = False
if env.get('PROJECTS_ENABLED', 'false').lower().strip() == 'true':
    PROJECTS_ENABLED = True

PROJECTS_AUTO_CREATE = False
if env.get('PROJECTS_AUTO_CREATE', 'false').lower().strip() == 'true':
    PROJECTS_AUTO_CREATE = True


# Salesforce integration

if env.get('SALESFORCE_INTEGRATION', 'false').lower().strip() == 'true':
    DATABASES = {
        **DATABASES,
        'salesforce': {
            'ENGINE': 'salesforce.backend',
            'CONSUMER_KEY': env.get('SALESFORCE_CONSUMER_KEY', ''),
            'CONSUMER_SECRET': env.get('SALESFORCE_CONSUMER_SECRET', ''),
            'USER': env.get('SALESFORCE_USER', ''),
            'PASSWORD': env.get('SALESFORCE_PASSWORD', ''),
            'HOST': env.get('SALESFORCE_LOGIN_URL', '')
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
if 'AWS_STORAGE_BUCKET_NAME' in env:
    FILE_FORM_TEMP_STORAGE = PRIVATE_FILE_STORAGE


# Matomo tracking

MATOMO_URL = env.get('MATOMO_URL', False)
MATOMO_SITEID = env.get('MATOMO_SITEID', False)
