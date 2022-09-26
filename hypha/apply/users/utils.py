from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def get_user_by_email(email, sensitive_search=1):
    UserModel = get_user_model()
    qs = UserModel.objects.filter(email__iexact=email)  # case insensitive matching

    # if multiple accounts then check with case sensitive search
    if len(qs) > 1 and sensitive_search:
        qs = qs.filter(email=email)  # case sensitive matching

    if len(qs) == 0:
        return

    user = qs[0]
    return user


def can_use_oauth_check(user):
    """
    Checks that the user belongs to the whitelisted domains.
    Anonymous or non-whitelisted email domains cannot log in
    or associate OAuth accounts
    """
    try:
        domain = user.email.split('@')[-1]
        return domain in settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS
    except AttributeError:
        # Anonymous user or setting not defined
        pass
    return False


def send_activation_email(user, site=None):
    """
    Send the activation email. The activation key is the username,
    signed using TimestampSigner.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    activation_path = reverse('users:activate', kwargs={'uidb64': uid, 'token': token})

    timeout_days = settings.PASSWORD_RESET_TIMEOUT // (24 * 3600)

    context = {
        'user': user,
        'name': user.get_full_name(),
        'username': user.get_username(),
        'activation_path': activation_path,
        'timeout_days': timeout_days,
        'org_long_name': settings.ORG_LONG_NAME,
        'org_short_name': settings.ORG_SHORT_NAME,
    }

    if site:
        context.update(site=site)

    subject = 'Account details for {username} at {org_long_name}'.format(**context)
    # Force subject to a single line to avoid header-injection issues.
    subject = ''.join(subject.splitlines())
    message = render_to_string('users/activation/email.txt', context)
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


def send_confirmation_email(user, token, updated_email=None, site=None):
    """
    Send the confirmation email. The confirmation token is the update email,
    signed using TimestampSigner.
    """

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    activation_path = reverse('users:confirm_email', kwargs={'uidb64': uid, 'token': token})

    timeout_days = settings.PASSWORD_RESET_TIMEOUT // (24 * 3600)

    context = {
        'user': user,
        'name': user.get_full_name(),
        'username': user.get_username(),
        'unverified_email': updated_email,
        'activation_path': activation_path,
        'timeout_days': timeout_days,
        'org_long_name': settings.ORG_LONG_NAME,
        'org_short_name': settings.ORG_SHORT_NAME,
    }

    if site:
        context.update(site=site)

    subject = 'Confirmation email for {unverified_email} at {org_long_name}'.format(**context)
    # Force subject to a single line to avoid header-injection issues.
    subject = ''.join(subject.splitlines())
    message = render_to_string('users/email_change/confirm_email.txt', context)
    if updated_email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [updated_email])
    else:
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
