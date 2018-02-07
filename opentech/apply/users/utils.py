from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


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


def send_activation_email(user, site):
    """
    Send the activation email. The activation key is the username,
    signed using TimestampSigner.
    """
    token_generator = PasswordResetTokenGenerator()
    context = {
        'user': user,
        'name': user.get_full_name(),
        'username': user.get_username(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': token_generator.make_token(user),
    }
    if site:
        context.update(site=site)

    subject = render_to_string('users/activation/email_subject.txt', context)
    # Force subject to a single line to avoid header-injection issues.
    subject = ''.join(subject.splitlines())
    message = render_to_string('users/activation/email.txt', context)
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)
