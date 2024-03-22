from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from wagtail.models import Site

from hypha.core.mail import MarkdownMail

from .models import PendingSignup
from .tokens import PasswordlessLoginTokenGenerator, PasswordlessSignupTokenGenerator
from .utils import get_redirect_url, get_user_by_email

User = get_user_model()


class PasswordlessAuthService:
    login_token_generator_class = PasswordlessLoginTokenGenerator
    signup_token_generator_class = PasswordlessSignupTokenGenerator

    next_url = None

    def __init__(self, request: HttpRequest, redirect_field_name: str = "next") -> None:
        self.redirect_field_name = redirect_field_name
        self.next_url = get_redirect_url(request, self.redirect_field_name)
        self.request = request
        self.site = Site.find_for_request(request)

    def _get_login_path(self, user):
        token = self.login_token_generator_class().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        login_path = reverse(
            "users:do_passwordless_login", kwargs={"uidb64": uid, "token": token}
        )

        if self.next_url:
            login_path = f"{login_path}?next={self.next_url}"

        return login_path

    def _get_signup_path(self, signup_obj):
        token = self.signup_token_generator_class().make_token(user=signup_obj)
        uid = urlsafe_base64_encode(force_bytes(signup_obj.pk))

        signup_path = reverse(
            "users:do_passwordless_signup", kwargs={"uidb64": uid, "token": token}
        )

        if self.next_url:
            signup_path = f"{signup_path}?next={self.next_url}"

        return signup_path

    def get_email_context(self) -> dict:
        return {
            "org_long_name": settings.ORG_LONG_NAME,
            "org_email": settings.ORG_EMAIL,
            "org_short_name": settings.ORG_SHORT_NAME,
            "site": self.site,
        }

    def send_email_no_account_found(self, to):
        context = self.get_email_context()
        subject = "Log in attempt at {org_long_name}".format(**context)
        # Force subject to a single line to avoid header-injection issues.
        subject = "".join(subject.splitlines())

        email = MarkdownMail("users/emails/passwordless_login_no_account_found.md")
        email.send(
            to=to,
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            context=context,
        )

    def send_login_email(self, user):
        login_path = self._get_login_path(user)
        timeout_minutes = self.login_token_generator_class().TIMEOUT // 60

        context = self.get_email_context()
        context.update(
            {
                "user": user,
                "is_active": user.is_active,
                "name": user.get_full_name(),
                "username": user.get_username(),
                "login_path": login_path,
                "timeout_minutes": timeout_minutes,
            }
        )

        subject = "Log in to {username} at {org_long_name}".format(**context)
        # Force subject to a single line to avoid header-injection issues.
        subject = "".join(subject.splitlines())

        email = MarkdownMail("users/emails/passwordless_login_email.md")
        email.send(
            to=user.email,
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            context=context,
        )

    def send_new_account_login_email(self, signup_obj):
        signup_path = self._get_signup_path(signup_obj)
        timeout_minutes = self.login_token_generator_class().TIMEOUT // 60

        context = self.get_email_context()
        context.update(
            {
                "signup_path": signup_path,
                "timeout_minutes": timeout_minutes,
            }
        )

        subject = "Welcome to {org_long_name}".format(**context)
        # Force subject to a single line to avoid header-injection issues.
        subject = "".join(subject.splitlines())

        email = MarkdownMail("users/emails/passwordless_new_account_login.md")
        email.send(
            to=signup_obj.email,
            subject=subject,
            from_email=settings.DEFAULT_FROM_EMAIL,
            context=context,
        )

    def initiate_login_signup(self, email: str) -> None:
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
        if user := get_user_by_email(email):
            self.send_login_email(user)
            return

        # No account found
        if not settings.ENABLE_PUBLIC_SIGNUP:
            self.send_email_no_account_found(email)
            return

        # Self registration is enabled
        signup_obj, _ = PendingSignup.objects.update_or_create(
            email=email,
            defaults={
                "token": get_random_string(32, "abcdefghijklmnopqrstuvwxyz0123456789")
            },
        )
        self.send_new_account_login_email(signup_obj)

        return True
