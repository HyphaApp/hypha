from django.conf import settings


def make_otf_staff(backend, user, response, *args, **kwargs):
    _, email_domain = user.email.split('@')
    if email_domain in settings.STAFF_EMAIL_DOMAINS:
        user.is_staff = True
        user.save()
