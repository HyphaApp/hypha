"""
Hypha project base settings.
"""

import os

import dj_database_url
from environs import Env

from .django import *  # noqa

env = Env()
env.read_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)


# Hypha custom settings

# Set the currency symbol to be used.
CURRENCY_CODE = env.str("CURRENCY_CODE", "USD")
CURRENCY_LOCALE = env.str("CURRENCY_LOCALE", "en_US")

# Default page pagination value.
DEFAULT_PER_PAGE = 20

# Form Rate-Limit Configuration
# DEFAULT_RATE_LIMIT is used by login, password, 2FA, etc
DEFAULT_RATE_LIMIT = env.str("DEFAULT_RATE_LIMIT", "5/m")

# IF Hypha should enforce 2FA for all users.
ENFORCE_TWO_FACTOR = env.bool("ENFORCE_TWO_FACTOR", False)

# Set the allowed file extension for all uploads fields.
FILE_ALLOWED_EXTENSIONS = [
    "doc",
    "docx",
    "odp",
    "ods",
    "odt",
    "pdf",
    "ppt",
    "pptx",
    "rtf",
    "txt",
    "xls",
    "xlsx",
]
FILE_ACCEPT_ATTR_VALUE = ", ".join(["." + ext for ext in FILE_ALLOWED_EXTENSIONS])

# Give staff lead permissions.
# Only effects setting external reviewers for now.
GIVE_STAFF_LEAD_PERMS = env.bool("GIVE_STAFF_LEAD_PERMS", False)

# Provide permissions for viewing archived submissions
SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF = env.bool(
    "SUBMISSIONS_ARCHIVED_ACCESS_STAFF", False
)
SUBMISSIONS_ARCHIVED_VIEW_ACCESS_STAFF_ADMIN = env.bool(
    "SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN", True
)

# Possible values are: "public_id" and "title"
SUBMISSION_TITLE_TEXT_TEMPLATE = env(
    "SUBMISSION_TITLE_TEMPLATE", default="{title} (#{public_id})"
)

# Provide permissions for archiving submissions
SUBMISSIONS_ARCHIVED_ACCESS_STAFF = env.bool("SUBMISSIONS_ARCHIVED_ACCESS_STAFF", False)
SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN = env.bool(
    "SUBMISSIONS_ARCHIVED_ACCESS_STAFF_ADMIN", True
)

# Enable staff to "hijack" (become) other users.
# Good for testing, might not be a good idea in production.
HIJACK_ENABLE = env.bool("HIJACK_ENABLE", False)

# Organisation name and e-mail address etc., used in e-mail templates etc.
ORG_EMAIL = env.str("ORG_EMAIL", "info@example.org")
ORG_GUIDE_URL = env.str("ORG_GUIDE_URL", "https://guide.example.org/")
ORG_LONG_NAME = env.str("ORG_LONG_NAME", "Acme Corporation")
ORG_SHORT_NAME = env.str("ORG_SHORT_NAME", "ACME")
ORG_URL = env.str("ORG_URL", "https://www.example.org/")

# Enable Projects in Hypha. Contracts and invoicing that comes after a submission is approved.
PROJECTS_ENABLED = env.bool("PROJECTS_ENABLED", False)

# Auto create projects for approved applications.
PROJECTS_AUTO_CREATE = env.bool("PROJECTS_AUTO_CREATE", False)

# Send out e-mail, slack messages etc. from Hypha. Set to true for production.
SEND_MESSAGES = env.bool("SEND_MESSAGES", False)

# If automatic e-mails should be sent out to reviewers when submissions are ready for review.
SEND_READY_FOR_REVIEW = env.bool("SEND_READY_FOR_REVIEW", True)

# Staff can upload the contract
STAFF_UPLOAD_CONTRACT = env.bool("STAFF_UPLOAD_CONTRACT", False)

# Slack settings.
SLACK_TOKEN = env.str("SLACK_TOKEN", None)
SLACK_USERNAME = env.str("SLACK_USERNAME", "Hypha")
SLACK_DESTINATION_ROOM = env.str("SLACK_DESTINATION_ROOM", None)
SLACK_DESTINATION_ROOM_COMMENTS = env.str("SLACK_DESTINATION_ROOM_COMMENTS", None)
SLACK_TYPE_COMMENTS = env.list("SLACK_TYPE_COMMENTS", [])
SLACK_ENDPOINT_URL = env.str(
    "SLACK_ENDPOINT_URL", "https://slack.com/api/chat.postMessage"
)
SLACK_BACKEND = (
    "django_slack.backends.CeleryBackend"  # UrllibBackend can be used for sync
)

# Activities email digest
ACTIVITY_DIGEST_RECIPIENT_EMAILS = env.list(
    "ACTIVITY_DIGEST_RECIPIENT_EMAILS", default=[]
)

# Staff e-mail domain. Used for OAUTH2 whitelist default value and staff account creation.
STAFF_EMAIL_DOMAINS = env.list("STAFF_EMAIL_DOMAINS", [])

# Should staff identities be obscured from Applicants & Partners (ie. comments will be ORG_LONG_NAME rather than John Doe).
HIDE_STAFF_IDENTITY = env.bool("HIDE_STAFF_IDENTITY", False)

# Should staff be able to access/see draft submissions.
SUBMISSIONS_DRAFT_ACCESS_STAFF = env.bool("SUBMISSIONS_DRAFT_ACCESS_STAFF", False)

# Should staff admins be able to access/see draft submissions.
SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN = env.bool(
    "SUBMISSIONS_DRAFT_ACCESS_STAFF_ADMIN", False
)

# Should staff be able to export submissions.
SUBMISSIONS_EXPORT_ACCESS_STAFF = env.bool("SUBMISSIONS_EXPORT_ACCESS_STAFF", False)

# Should staff admins be able to export submissions.
SUBMISSIONS_EXPORT_ACCESS_STAFF_ADMIN = env.bool(
    "SUBMISSIONS_EXPORT_ACCESS_STAFF_ADMIN", True
)

# Columns to exclude from the submission tables.
# Possible values are: fund, round, status, lead, reviewers, screening_statuses, category_options, meta_terms, organization_name
SUBMISSIONS_TABLE_EXCLUDED_FIELDS = env.list(
    "SUBMISSIONS_TABLE_EXCLUDED_FIELDS", ["organization_name"]
)

# Should submission automatically transition after all reviewer roles are assigned.
TRANSITION_AFTER_ASSIGNED = env.bool("TRANSITION_AFTER_ASSIGNED", False)

# Should submission automatically transition after n number of reviews.
# Possible values are: False, 1,2,3,…
TRANSITION_AFTER_REVIEWS = env.bool("TRANSITION_AFTER_REVIEWS", False)

# Default visibility for reviews.
REVIEW_VISIBILITY_DEFAULT = env.str("REVIEW_VISIBILITY_DEFAULT", "private")

# Require an applicant to view their rendered application before submitting
SUBMISSION_PREVIEW_REQUIRED = env.bool("SUBMISSION_PREVIEW_REQUIRED", True)

# Allow Withdrawing of Submissions
ENABLE_SUBMISSION_WITHDRAWAL = env.bool("ENABLE_SUBMISSION_WITHDRAWAL", False)

# Project settings.

# SECRET_KEY is required
SECRET_KEY = env.str("SECRET_KEY", None)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", [])

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
APP_NAME = env.str("APP_NAME", "hypha")
DATABASES = {
    "default": dj_database_url.config(
        default=f"postgres:///{APP_NAME}", conn_max_age=600, conn_health_checks=True
    )
}

# https://docs.djangoproject.com/en/4.1/ref/settings/#conn-health-checks
# Setting this to True, as we are using a non-zero valve for conn_max_age in dj_database_url.config
CONN_HEALTH_CHECKS = env.bool("CONN_HEALTH_CHECKS", True)

# Language code in standard language id format: en, en-gb, en-us
# The corrosponding locale dir is named: en, en_GB, en_US
LANGUAGE_CODE = env.str("LANGUAGE_CODE", "en")

# Number of seconds that password reset and account activation links are valid (default 259200, 3 days).
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", 259200)

# Timeout for passwordless login links (default 900, 15 minutes).
PASSWORDLESS_LOGIN_TIMEOUT = env.int("PASSWORDLESS_LOGIN_TIMEOUT", 900)  # 15 minutes

# Enable users to create accounts without submitting an application.
ENABLE_PUBLIC_SIGNUP = env.bool("ENABLE_PUBLIC_SIGNUP", True)

# Forces users to log in first in order to make an application.  This is particularly useful in conjunction
# with ENABLE_PUBLIC_SIGNUP
# @deprecated: This setting is deprecated and will be removed in a future release.
FORCE_LOGIN_FOR_APPLICATION = env.bool("FORCE_LOGIN_FOR_APPLICATION", True)

# Timeout for passwordless signup links (default 900, 15 minutes).
PASSWORDLESS_SIGNUP_TIMEOUT = env.int("PASSWORDLESS_SIGNUP_TIMEOUT", 900)  # 15 minutes

# Seconds to enter password on password page while email change/2FA change (default 120).
PASSWORD_PAGE_TIMEOUT = env.int("PASSWORD_PAGE_TIMEOUT", 120)

#  Template engines and options to be used with Django.
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(PROJECT_DIR, "templates_custom"),
            os.path.join(PROJECT_DIR, "templates"),
            os.path.join(PROJECT_DIR, "apply", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "hypha.apply.projects.context_processors.projects_enabled",
                "hypha.cookieconsent.context_processors.cookies_accepted",
                "hypha.core.context_processors.global_vars",
            ],
            "builtins": [
                "django_web_components.templatetags.components",
            ],
        },
    },
]


# Email settings

EMAIL_HOST = env.str("EMAIL_HOST", None)
EMAIL_PORT = env.int("EMAIL_PORT", None)
EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", None)
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", None)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", False)
EMAIL_SUBJECT_PREFIX = env.str("EMAIL_SUBJECT_PREFIX", "")
SERVER_EMAIL = DEFAULT_FROM_EMAIL = env.str("SERVER_EMAIL", None)


# Cache settings

# Set max-age header.
CACHE_CONTROL_MAX_AGE = env.int("CACHE_CONTROL_MAX_AGE", 3600)

# Set s-max-age header that is used by reverse proxy/front end cache.
CACHE_CONTROL_S_MAXAGE = env.int("CACHE_CONTROL_S_MAXAGE", 3600)

# Set feed cache timeout (automatic cache refresh).
FEED_CACHE_TIMEOUT = 600

# Set X-Frame-Options header for every outgoing HttpResponse
X_FRAME_OPTIONS = "SAMEORIGIN"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "database_cache",
    },
}

# Use a more permanent cache for django-file-form.
# It uses it to store metadata about files while they are being uploaded.
# This might reduce the likelihood of any interruptions on heroku.
# NB It doesn't matter what the `KEY_PREFIX` is,
# `clear_cache` will clear all caches with the same `LOCATION`.
CACHES["django_file_form"] = {
    "BACKEND": "django.core.cache.backends.db.DatabaseCache",
    "LOCATION": "database_cache",
    "KEY_PREFIX": "django_file_form",
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static_compiled"),
    os.path.join(PROJECT_DIR, "../public"),
]

STATIC_ROOT = env.str("STATIC_DIR", os.path.join(BASE_DIR, "static"))
STATIC_URL = env.str("STATIC_URL", "/static/")

MEDIA_ROOT = env.str("MEDIA_DIR", os.path.join(BASE_DIR, "media"))
MEDIA_URL = env.str("MEDIA_URL", "/media/")


# Wagtail settings

WAGTAIL_FRONTEND_LOGIN_URL = "/auth/"
WAGTAIL_SITE_NAME = "hypha"
WAGTAILIMAGES_IMAGE_MODEL = "images.CustomImage"
WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = False
WAGTAIL_USER_EDIT_FORM = "hypha.apply.users.forms.CustomUserEditForm"
WAGTAIL_USER_CREATION_FORM = "hypha.apply.users.forms.CustomUserCreationForm"
WAGTAIL_USER_CUSTOM_FIELDS = ["full_name"]
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False
WAGTAILUSERS_PASSWORD_ENABLED = False
WAGTAILUSERS_PASSWORD_REQUIRED = False
WAGTAILEMBEDS_RESPONSIVE_HTML = True
PASSWORD_REQUIRED_TEMPLATE = "password_required.html"

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    "default": {
        "WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea",
        "OPTIONS": {
            "features": [
                "bold",
                "italic",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "ol",
                "ul",
                "link",
            ]
        },
    },
}

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
    },
}

# Cloudflare cache invalidation.
# See https://docs.wagtail.io/en/v2.8/reference/contrib/frontendcache.html
if env.str("CLOUDFLARE_BEARER_TOKEN", None) and env.str("CLOUDFLARE_API_ZONEID"):
    INSTALLED_APPS += ("wagtail.contrib.frontend_cache",)  # noqa
    WAGTAILFRONTENDCACHE = {
        "cloudflare": {
            "BACKEND": "wagtail.contrib.frontend_cache.backends.CloudflareBackend",
            "BEARER_TOKEN": env.str("CLOUDFLARE_BEARER_TOKEN"),
            "ZONEID": env.str("CLOUDFLARE_API_ZONEID"),
        },
    }


# Social Auth settings

# Set the Google OAuth2 credentials in ENV variables or local.py
# To create a new set of credentials, go to https://console.developers.google.com/apis/credentials
# Make sure the Google+ API is enabled for your API project
SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS = env.list(
    "SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS", STAFF_EMAIL_DOMAINS
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env.str("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")

SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_LOGIN_ERROR_URL = "users:login"
SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL = "users:account"

# For pipelines, see http://python-social-auth.readthedocs.io/en/latest/pipeline.html?highlight=pipelines#authentication-pipeline
# Create / associate accounts (including by email)
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

# NH3 Settings

NH3_ALLOWED_TAGS = [
    "a",
    "b",
    "big",
    "blockquote",
    "br",
    "cite",
    "code",
    "col",
    "colgroup",
    "dd",
    "del",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "ins",
    "li",
    "ol",
    "p",
    "pre",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
]

NH3_ALLOWED_ATTRIBUTES = {
    "*": [
        "class",
        "colspan",
        "href",
        "rowspan",
        "target",
        "title",
        "width",
        "data-tippy-content",
    ]
}

NH3_STRIP_COMMENTS = True


# Hijack Settings

HIJACK_LOGIN_REDIRECT_URL = "/dashboard/"
HIJACK_LOGOUT_REDIRECT_URL = "/account/"
HIJACK_DECORATOR = "hypha.apply.users.decorators.superuser_decorator"
HIJACK_PERMISSION_CHECK = "hijack.permissions.superusers_and_staff"


# Celery settings

CELERY_TASK_ALWAYS_EAGER = True


# S3 settings

if env.str("AWS_STORAGE_BUCKET_NAME", None):
    DEFAULT_FILE_STORAGE = "hypha.storage_backends.PublicMediaStorage"
    PRIVATE_FILE_STORAGE = "hypha.storage_backends.PrivateMediaStorage"
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
    AWS_PUBLIC_BUCKET_NAME = env.str("AWS_PUBLIC_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME)
    AWS_PRIVATE_BUCKET_NAME = env.str(
        "AWS_PRIVATE_BUCKET_NAME", AWS_STORAGE_BUCKET_NAME
    )
    AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN", None)
    AWS_PRIVATE_CUSTOM_DOMAIN = env.str("AWS_PRIVATE_CUSTOM_DOMAIN", None)
    AWS_QUERYSTRING_EXPIRE = env.str("AWS_QUERYSTRING_EXPIRE", None)
    AWS_PUBLIC_CUSTOM_DOMAIN = env.str("AWS_PUBLIC_CUSTOM_DOMAIN", None)
    INSTALLED_APPS += ("storages",)

# Settings to connect to the Bucket from which we are migrating data
AWS_MIGRATION_BUCKET_NAME = env.str("AWS_MIGRATION_BUCKET_NAME", "")
AWS_MIGRATION_ACCESS_KEY_ID = env.str("AWS_MIGRATION_ACCESS_KEY_ID", "")
AWS_MIGRATION_SECRET_ACCESS_KEY = env.str("AWS_MIGRATION_SECRET_ACCESS_KEY", "")

# Apply nav items settings

APPLY_NAV_MENU_ITEMS = env.json("APPLY_NAV_MENU_ITEMS", "{}")
APPLY_NAV_SUBMISSIONS_ITEMS = env.json("APPLY_NAV_SUBMISSIONS_ITEMS", "{}")
APPLY_NAV_PROJECTS_ITEMS = env.json("APPLY_NAV_PROJECTS_ITEMS", "{}")

# Basic auth settings
if env.bool("BASIC_AUTH_ENABLED", False):
    MIDDLEWARE.insert(0, "baipw.middleware.BasicAuthIPWhitelistMiddleware")
    BASIC_AUTH_LOGIN = env.str("BASIC_AUTH_LOGIN", None)
    BASIC_AUTH_PASSWORD = env.str("BASIC_AUTH_PASSWORD", None)
    BASIC_AUTH_WHITELISTED_HTTP_HOSTS = env.list(
        "BASIC_AUTH_WHITELISTED_HTTP_HOSTS", []
    )
    BASIC_AUTH_WHITELISTED_IP_NETWORKS = env.list(
        "BASIC_AUTH_WHITELISTED_IP_NETWORKS", []
    )

# Sessions
# https://docs.djangoproject.com/en/stable/ref/settings/#sessions

# The default age of session cookies, in seconds.
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", 60 * 60 * 12)  # 12 hours

# The age of session cookies when users check "Remember me" etc., in seconds.
SESSION_COOKIE_AGE_LONG = env.int(
    "SESSION_COOKIE_AGE_LONG", 60 * 60 * 24 * 7 * 2
)  # 2 weeks

# This is used by Wagtail's email notifications for constructing absolute URLs.
PRIMARY_HOST = env.str("PRIMARY_HOST", None)
WAGTAILADMIN_BASE_URL = env.str("WAGTAILADMIN_BASE_URL", None) or (
    f"https://{PRIMARY_HOST}" if PRIMARY_HOST else None
)


# Security settings
# https://docs.djangoproject.com/en/stable/ref/middleware/#module-django.middleware.security

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", None)
SECURE_BROWSER_XSS_FILTER = env.bool("SECURE_BROWSER_XSS_FILTER", True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("SECURE_CONTENT_TYPE_NOSNIFF", True)

if env.bool("COOKIE_SECURE", False):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    ELEVATE_COOKIE_SECURE = True

# Referrer-policy header settings
# https://django-referrer-policy.readthedocs.io/en/1.0/

REFERRER_POLICY = env.str(
    "SECURE_REFERRER_POLICY", "no-referrer-when-downgrade"
).strip()

# Django Elevate settings
# https://django-elevate.readthedocs.io/en/latest/config/index.html

# How long should Elevate mode be active for?
ELEVATE_COOKIE_AGE = env.int("ELEVATE_COOKIE_AGE", 3600)  # 1 hours

# An extra salt to be added into the cookie signature.
ELEVATE_COOKIE_SALT = env.str("ELEVATE_COOKIE_SALT", SECRET_KEY)


# Rest Framework settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}


# django-file-form settings

FILE_FORM_CACHE = "django_file_form"
FILE_FORM_UPLOAD_DIR = "temp_uploads"
# Ensure FILE_FORM_UPLOAD_DIR exists:
os.makedirs(os.path.join(MEDIA_ROOT, FILE_FORM_UPLOAD_DIR), exist_ok=True)
# Store temporary files on S3 too (files are still uploaded to local filesystem first)
if env.str("AWS_STORAGE_BUCKET_NAME", None):
    FILE_FORM_TEMP_STORAGE = PRIVATE_FILE_STORAGE


# Sage IntAcct integration settings

INTACCT_ENABLED = env.bool("INTACCT_ENABLED", False)
INTACCT_SENDER_ID = env.str("INTACCT_SENDER_ID", "")
INTACCT_SENDER_PASSWORD = env.str("INTACCT_SENDER_PASSWORD", "")
INTACCT_USER_ID = env.str("INTACCT_USER_ID", "")
INTACCT_COMPANY_ID = env.str("INTACCT_COMPANY_ID", "")
INTACCT_USER_PASSWORD = env.str("INTACCT_USER_PASSWORD", "")

# Finance extension to finance2 for Project Invoicing
INVOICE_EXTENDED_WORKFLOW = env.bool("INVOICE_EXTENDED_WORKFLOW", True)


# Misc settings

# Use Pillow to create QR codes so they are PNG and not SVG.
# Apples Safari on iOS and macOS can then recognise them automatically.
# TWO_FACTOR_QR_FACTORY = 'qrcode.image.pil.PilImage'

LOCALE_PATHS = (PROJECT_DIR + "/locale",)

DEBUG = False
DEBUGTOOLBAR = False

if not SEND_MESSAGES:
    from django.contrib.messages import constants as message_constants

    MESSAGE_LEVEL = message_constants.DEBUG

# Django countries package provides ISO 3166-1 countries which does not contain Kosovo.
COUNTRIES_OVERRIDE = {
    "KV": "Kosovo",
}

# Google Translate
ENABLE_GOOGLE_TRANSLATE = env.bool("ENABLE_GOOGLE_TRANSLATE", True)

# Sentry configuration.
# -----------------------------------------------------------------------------
SENTRY_DSN = env.str("SENTRY_DSN", None)
SENTRY_PUBLIC_KEY = env.str("SENTRY_PUBLIC_KEY", None)
SENTRY_TRACES_SAMPLE_RATE = env.float("SENTRY_TRACES_SAMPLE_RATE", default=0)
SENTRY_ENVIRONMENT = env.str("SENTRY_ENVIRONMENT", "production")
SENTRY_DEBUG = env.bool("SENTRY_DEBUG", False)
SENTRY_DENY_URLS = env.list("SENTRY_DENY_URLS", default=[])

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        debug=SENTRY_DEBUG,
        integrations=[DjangoIntegration()],
    )
