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
