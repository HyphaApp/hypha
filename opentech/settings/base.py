"""
Django settings for opentech project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

env = os.environ.copy()

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)


# Application definition

INSTALLED_APPS = [
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

    'hijack',
    'compat',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.postgres',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.forms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

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
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'opentech',
    }
}


# Cache
# Use database cache as the cache backend

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'database_cache',
    }
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
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
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

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, 'static_compiled'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

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
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] (%(process)d/%(thread)d) %(name)s %(levelname)s: %(message)s'
        }
    },
    'loggers': {
        'opentech': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
        'wagtail': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
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

# Social Auth
SOCIAL_AUTH_URL_NAMESPACE = 'social'

# Set the Google OAuth2 credentials in ENV variables or local.py
# To create a new set of credentials, go to https://console.developers.google.com/apis/credentials
# Make sure the Google+ API is enabled for your API project
STAFF_EMAIL_DOMAINS = ['opentech.fund']
SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = STAFF_EMAIL_DOMAINS
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

SOCIAL_AUTH_LOGIN_ERROR_URL = 'users_public:login'
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = 'users:account'

# For pipelines, see http://python-social-auth.readthedocs.io/en/latest/pipeline.html?highlight=pipelines#authentication-pipeline
# Create / associate accounts (including by email)
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
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

    INSTALLED_APPS += (
        'storages',
    )


MAILCHIMP_API_KEY = env.get('MAILCHIMP_API_KEY')
MAILCHIMP_LIST_ID = env.get('MAILCHIMP_LIST_ID')
