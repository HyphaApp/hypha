from django.conf import settings
from django.contrib.auth.models import Group


def make_otf_staff(backend, user, response, *args, **kwargs):
    _, email_domain = user.email.split('@')
    if email_domain in settings.STAFF_EMAIL_DOMAINS:
        staff_group = Group.objects.get('Staff')
        user.groups.add(staff_group)
