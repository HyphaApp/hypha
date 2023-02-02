# Configuration

Under hypha/settings/ there are several python configuration files:

We highly recommend using environment variables since it is more secure. It is also possible to add values to settings in a `local.py` files, see below.

* base.py – Base settings file. Other settings file start by loading this in.
* django-py - Django settings, loaded by base.py. Separated out to make base.py more manageable.
* dev.py – This is settings for development work.
* example.py – Example settings, not loaded anywhere. (This file should be expanded to cover more settings.)
* local.py.example – Copy and rename to "local.py" and it will be loaded by both production and dev settings. Main use is to allow developers an easy way to set and test settings. Can also be used in production but environment variables are the preferred and more secure way.
* production.py – This is settings for production use.
* test.py – This is the settings file for running tests.


## Project settings.

### SECRET_KEY is required

    SECRET_KEY = env.str('SECRET_KEY', None)

### ALLOWED_HOSTS is required

    ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', [])

### Database

See <https://docs.djangoproject.com/en/stable/ref/settings/#databases>

We use `dj-database-url` so also see <https://github.com/jazzband/dj-database-url>

Be default Hypha looks for a database with the name "hypha". Set `APP_NAME` to change the database name.

    APP_NAME = env.str('APP_NAME', 'hypha')
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            default=f'postgres:///{APP_NAME}'
        )
    }

### Language code in standard language id format: en, en-gb, en-us

The corrosponding locale dir is named: en, en_GB, en_US

    LANGUAGE_CODE = env.str('LANGUAGE_CODE', 'en')

### Number of seconds that password reset and account activation links are valid (default 259200, 3 days).

    PASSWORD_RESET_TIMEOUT = env.int('PASSWORD_RESET_TIMEOUT', 259200)

### Seconds to enter password on password page while email change/2FA change (default 120).

    PASSWORD_PAGE_TIMEOUT = env.int('PASSWORD_PAGE_TIMEOUT', 120)


## Hypha custom settings

### Set the currency symbol to be used.

    CURRENCY_SYMBOL = env.str('CURRENCY_SYMBOL', '$')

### Default page pagination value.

    DEFAULT_PER_PAGE = 20

### Webpack bundle loader. When set to False, the React app part of Hypha is disabled.

    ENABLE_WEBPACK_BUNDLES = env.bool('ENABLE_WEBPACK_BUNDLES', True)

### If Hypha should enforce 2FA for all users.

    ENFORCE_TWO_FACTOR = env.bool('ENFORCE_TWO_FACTOR', False)

### Set the allowed file extension for all uploads fields.

    FILE_ALLOWED_EXTENSIONS = ['doc', 'docx', 'odp', 'ods', 'odt', 'pdf', 'ppt', 'pptx', 'rtf', 'txt', 'xls', 'xlsx']
    FILE_ACCEPT_ATTR_VALUE = ', '.join(['.' + ext for ext in FILE_ALLOWED_EXTENSIONS])

### Give staff lead permissions.

Only effects setting external reviewers for now.

    GIVE_STAFF_LEAD_PERMS = env.bool('GIVE_STAFF_LEAD_PERMS', False)

### Enable staff to "hijack" (become) other users.

Good for testing, might not be a good idea in production.

    HIJACK_ENABLE = env.bool('HIJACK_ENABLE', False)

### Matomo tracking.

    MATOMO_SITEID = env.str('MATOMO_SITEID', None)
    MATOMO_URL = env.str('MATOMO_URL', None)

### Organisation name and e-mail address etc., used in e-mail templates etc.

    ORG_EMAIL = env.str('ORG_EMAIL', 'info@example.org')
    ORG_GUIDE_URL = env.str('ORG_GUIDE_URL', 'https://guide.example.org/')
    ORG_LONG_NAME = env.str('ORG_LONG_NAME', 'Acme Corporation')
    ORG_SHORT_NAME = env.str('ORG_SHORT_NAME', 'ACME')
    ORG_URL = env.str('ORG_URL', 'https://www.example.org/')

### Enable Projects in Hypha. Contracts and invoicing that comes after a submission is approved.

    PROJECTS_ENABLED = env.bool('PROJECTS_ENABLED', False)

### Auto create projects for approved applications.

    PROJECTS_AUTO_CREATE = env.bool('PROJECTS_AUTO_CREATE', False)

### Send out e-mail, slack messages etc. from Hypha. Set to true for production.

    SEND_MESSAGES = env.bool('SEND_MESSAGES', False)

### If automatic e-mails should be sent out to reviewers when submissions are ready for review.

    SEND_READY_FOR_REVIEW = env.bool('SEND_READY_FOR_REVIEW', True)

### Slack settings.

    SLACK_TOKEN = env.str('SLACK_TOKEN', None)
    SLACK_USERNAME = env.str('SLACK_USERNAME', 'Hypha')
    SLACK_DESTINATION_ROOM = env.str('SLACK_DESTINATION_ROOM', None)
    SLACK_DESTINATION_ROOM_COMMENTS = env.str('SLACK_DESTINATION_ROOM_COMMENTS', None)
    SLACK_TYPE_COMMENTS = env.list('SLACK_TYPE_COMMENTS', [])
    SLACK_ENDPOINT_URL = env.str('SLACK_ENDPOINT_URL', 'https://slack.com/api/chat.postMessage')
    SLACK_BACKEND = 'django_slack.backends.CeleryBackend'  # UrllibBackend can be used for sync

### Staff e-mail domain. Used for OAUTH2 whitelist default value and staff account creation.

    STAFF_EMAIL_DOMAINS = env.list('STAFF_EMAIL_DOMAINS', [])

### Should staff be able to access/see draft submissions.

    SUBMISSIONS_DRAFT_ACCESS_STAFF = env.bool('SUBMISSIONS_DRAFT_ACCESS_STAFF', False)

### Columns to exclude from the submission tables.

Possible values are: fund, round, status, lead, reviewers, screening_statuses, category_options, meta_terms

    SUBMISSIONS_TABLE_EXCLUDED_FIELDS = env.list('SUBMISSIONS_TABLE_EXCLUDED_FIELDS', [])

### Should submission automatically transition after all reviewer roles are assigned.

    TRANSITION_AFTER_ASSIGNED = env.bool('TRANSITION_AFTER_ASSIGNED', False)

### Should submission automatically transition after n number of reviews.

Possible values are: False, 1,2,3,…

    TRANSITION_AFTER_REVIEWS = env.bool('TRANSITION_AFTER_REVIEWS', False)

### On Heroku, set to true if deploying to Heroku.

    env.bool('ON_HEROKU', False)


### Secure cookies

Set this to enable Djangos settings for secure cookies.

    COOKIE_SECURE = env.bool('COOKIE_SECURE', False)


## E-mail settings


### From e-mail address

    SERVER_EMAIL = DEFAULT_FROM_EMAIL = env.str('SERVER_EMAIL', None)

### E-mail subject prefix

    EMAIL_SUBJECT_PREFIX = env.str('EMAIL_SUBJECT_PREFIX', None)

### Anymail

Hypha uses the Anymail packaged so a number of mail backends are supported. Mailgun settings are present in the production file by default.

Read more about Anymail: <https://anymail.dev/en/stable/>

    MAILGUN_API_KEY = env.str('MAILGUN_API_KEY')
    MAILGUN_SENDER_DOMAIN = env.str('EMAIL_HOST', None)
    MAILGUN_API_URL = env.str('MAILGUN_API_URL', 'https://api.mailgun.net/v3')
    WEBHOOK_SECRET = env.str('ANYMAIL_WEBHOOK_SECRET', None)

### Local e-mail server

It is also possible to use a local e-mail server.

    EMAIL_HOST = env.str('EMAIL_HOST', None)
    EMAIL_PORT = env.int('EMAIL_PORT', None)
    EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', None)
    EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', None)
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', False)
    EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', False)


## Sentry configuration.

Track errors from your Hypha installation.

    SENTRY_DSN = env.str('SENTRY_DSN', None)


## S3 settings

    AWS_ACCESS_KEY_ID = env.str('AWS_ACCESS_KEY_ID', None)
    AWS_SECRET_ACCESS_KEY = env.str('AWS_SECRET_ACCESS_KEY', None)
    AWS_STORAGE_BUCKET_NAME = env.str('AWS_STORAGE_BUCKET_NAME', None)
    AWS_PRIVATE_CUSTOM_DOMAIN = env.str('AWS_PRIVATE_CUSTOM_DOMAIN', None)
    AWS_QUERYSTRING_EXPIRE = env.str('AWS_QUERYSTRING_EXPIRE', None)

## Basic auth settings

It is possible to set Hypha behind basic authentication with IP whitelisting support. Good for test sites etc.

See <https://github.com/tm-kn/django-basic-auth-ip-whitelist>

    BASIC_AUTH_LOGIN = env.str('BASIC_AUTH_LOGIN', None)
    BASIC_AUTH_PASSWORD = env.str('BASIC_AUTH_PASSWORD', None)
    BASIC_AUTH_WHITELISTED_HTTP_HOSTS = env.list('BASIC_AUTH_WHITELISTED_HTTP_HOSTS', [])
    BASIC_AUTH_WHITELISTED_IP_NETWORKS = env.list('BASIC_AUTH_WHITELISTED_IP_NETWORKS', [])
