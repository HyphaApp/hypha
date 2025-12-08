from typing import Optional

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

    def __init__(
        self,
        request: HttpRequest,
        redirect_field_name: Optional[str] = "next",
        extended_session: Optional[bool] = False,
    ) -> None:
        """The service utilized to handle passwordless auth requests.

        Determines if a user is logging in or signing up, and sends the appropriate magic links.

        Args:
            request: HttpRequest object.
            redirect_field: The name of a field containing the redirect URL.
            extended_session: Include the `remember-me` param in the magic link, defaults to False.
        """
        self.redirect_field_name = redirect_field_name
        self.next_url = get_redirect_url(request, self.redirect_field_name)
        self.extended_session = extended_session
        self.request = request
        self.site = Site.find_for_request(request)

    def _get_login_path(self, user):
        token = self.login_token_generator_class().make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        login_path = reverse(
            "users:do_passwordless_login", kwargs={"uidb64": uid, "token": token}
        )

        if params := self._get_url_params():
            login_path = f"{login_path}?{params}"

        return login_path

    def _get_signup_path(self, signup_obj):
        token = self.signup_token_generator_class().make_token(user=signup_obj)
        uid = urlsafe_base64_encode(force_bytes(signup_obj.pk))

        signup_path = reverse(
            "users:do_passwordless_signup", kwargs={"uidb64": uid, "token": token}
        )

        if params := self._get_url_params():
            signup_path = f"{signup_path}?{params}"

        return signup_path

    def _get_url_params(self) -> None | str:
        """Gets a URL encoded string of params for the magic link

        Populates the redirect url & remember me params if they exist

        Returns:
            A url encoded string if params exist, `None` otherwise.
        """
        params = []

        # Utilized this instead of QueryDict to allow `remember-me` to not need a value.
        # Redundant to have a useless value (ie. `remember-me=1`) when the login view only checks for the key
        if self.next_url:
            params.append(f"next={self.next_url}")
        if self.extended_session:
            params.append("remember-me")

        if params:
            return "&".join(params)

        return None

    def send_email_no_account_found(self, to):
        subject = f"Log in attempt at {settings.ORG_LONG_NAME}"
        # Force subject to a single line to avoid header-injection issues.
        subject = "".join(subject.splitlines())

        email = MarkdownMail("users/emails/passwordless_login_no_account_found.md")
        email.send(to=to, subject=subject, from_email=settings.DEFAULT_FROM_EMAIL)

    def send_login_email(self, user):
        login_path = self._get_login_path(user)
        timeout_minutes = self.login_token_generator_class().TIMEOUT // 60

        context = {
            "user": user,
            "is_active": user.is_active,
            "name": user.get_full_name(),
            "username": user.get_username(),
            "login_path": login_path,
            "timeout_minutes": timeout_minutes,
        }

        subject = f"Log in to {user.get_username()} at {settings.ORG_LONG_NAME}"
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

        context = {
            "signup_path": signup_path,
            "timeout_minutes": timeout_minutes,
        }

        subject = f"Welcome to {settings.ORG_LONG_NAME}"
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
