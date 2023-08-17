from django.conf import settings
from django.http import HttpRequest
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from wagtail.models import Site

from hypha.core.mail import MarkdownMail

from .tokens import PasswordlessLoginTokenGenerator
from .utils import get_user_by_email


def send_passwordless_login_signup_email(
    email: str,
    request: HttpRequest,
    next_url: str = None
) -> None:
    """Send a passwordless login/signup email.

    If the user exists, send a login email. If the user does not exist, send a
    signup invite email.

    Args:
        email: Email address to send the email to.
        request: HttpRequest object.
        next_url: URL to redirect to after login/signup. Defaults to None.

    Returns:
        None
    """
    user = get_user_by_email(email)
    if user:
        token_generator = PasswordlessLoginTokenGenerator()
        token = token_generator.make_token(user)

        uid = urlsafe_base64_encode(force_bytes(user.pk))

        activation_path = reverse('users:do_passwordless_login', kwargs={'uidb64': uid, 'token': token})
        if next_url:
            activation_path = f'{activation_path}?next={next_url}'

        timeout_hours = token_generator.PASSWORDLESS_LOGIN_TIMEOUT // 3600

        context = {
            'user': user,
            'name': user.get_full_name(),
            'username': user.get_username(),
            'activation_path': activation_path,
            'timeout_hours': timeout_hours,
            'org_long_name': settings.ORG_LONG_NAME,
            'org_short_name': settings.ORG_SHORT_NAME,
        }

        if site := Site.find_for_request(request):
            context.update(site=site)

        subject = 'Login to {username} at {org_long_name}'.format(**context)
        # Force subject to a single line to avoid header-injection issues.
        subject = ''.join(subject.splitlines())

        email = MarkdownMail('users/passwordless_login_email.md')
        email.send(
            to=user.email,
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            context=context,
        )

    return user
