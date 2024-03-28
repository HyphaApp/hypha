import string

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _


def get_user_by_email(email):
    UserModel = get_user_model()
    qs = UserModel.objects.filter(email__iexact=email)  # case insensitive matching

    # if multiple accounts then check with case sensitive search
    if len(qs) > 1:
        qs = qs.filter(email=email)  # case sensitive matching

    if len(qs) == 0:
        return

    user = qs[0]
    return user


def is_user_already_registered(email: str) -> (bool, str):
    """
    Checks if a specified user is already registered.
    Returns a tuple containing a boolean value that indicates if the user exists
    and in case he does whats the duplicated attribute
    """

    user_model = get_user_model()
    if user_model.objects.filter(email__iexact=email):
        return (True, _("Email is already in use."))

    return (False, "")


def can_use_oauth_check(user):
    """
    Checks that the user belongs to the whitelisted domains.
    Anonymous or non-whitelisted email domains cannot log in
    or associate OAuth accounts
    """
    try:
        domain = user.email.split("@")[-1]
        return domain in settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS
    except AttributeError:
        # Anonymous user or setting not defined
        pass
    return False


def send_activation_email(
    user,
    site=None,
    email_template="users/activation/email.txt",
    email_subject_template="users/activation/email_subject.txt",
    redirect_url="",
):
    """
    Send the activation email. The activation key is the username,
    signed using TimestampSigner.
    """
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    activation_path = reverse("users:activate", kwargs={"uidb64": uid, "token": token})
    if redirect_url:
        activation_path = f"{activation_path}?next={redirect_url}"

    timeout_days = settings.PASSWORD_RESET_TIMEOUT // (24 * 3600)

    context = {
        "user": user,
        "name": user.get_full_name(),
        "username": user.get_username(),
        "activation_path": activation_path,
        "timeout_days": timeout_days,
        "org_long_name": settings.ORG_LONG_NAME,
        "org_short_name": settings.ORG_SHORT_NAME,
    }

    if site:
        context.update(site=site)

    subject = render_to_string(email_subject_template, context)
    # Force subject to a single line to avoid header-injection issues.
    subject = "".join(subject.splitlines())
    message = render_to_string(email_template, context)
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


def send_confirmation_email(user, token, updated_email=None, site=None):
    """
    Send the confirmation email. The confirmation token is the update email,
    signed using TimestampSigner.
    """

    uid = urlsafe_base64_encode(force_bytes(user.pk))

    activation_path = reverse(
        "users:confirm_email", kwargs={"uidb64": uid, "token": token}
    )

    timeout_days = settings.PASSWORD_RESET_TIMEOUT // (24 * 3600)

    context = {
        "user": user,
        "name": user.get_full_name(),
        "username": user.get_username(),
        "unverified_email": updated_email,
        "activation_path": activation_path,
        "timeout_days": timeout_days,
        "org_long_name": settings.ORG_LONG_NAME,
        "org_short_name": settings.ORG_SHORT_NAME,
    }

    if site:
        context.update(site=site)

    subject = "Confirmation email for {unverified_email} at {org_long_name}".format(
        **context
    )
    # Force subject to a single line to avoid header-injection issues.
    subject = "".join(subject.splitlines())
    message = render_to_string("users/email_change/confirm_email.txt", context)
    if updated_email:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [updated_email])
    else:
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


def get_redirect_url(
    request, redirect_field: str, success_url_allowed_hosts=None
) -> str:
    """
    Return the user-originating redirect URL if it's safe.

    Args:
        request (HttpRequest): The request object.
        redirect_field (str): The name of a field containing the redirect URL.
        success_url_allowed_hosts (set): A set of allowed hosts for the redirect URL.
    """
    # If no allowed hosts are provided, use settings.ALLOWED_HOSTS
    if success_url_allowed_hosts is None:
        success_url_allowed_hosts = set(settings.ALLOWED_HOSTS)

    # Try to get the redirect URL from the request's POST data, and if it's not
    # there, try to get it from the request's GET data. If it's not in either,
    # default to an empty string.
    redirect_to = request.POST.get(redirect_field, request.GET.get(redirect_field, ""))

    # Check if the redirect URL is safe. If it is, return it. Otherwise, return
    # an empty string.
    url_is_safe = url_has_allowed_host_and_scheme(
        url=redirect_to,
        allowed_hosts={request.get_host(), *success_url_allowed_hosts},
        require_https=request.is_secure(),
    )
    return redirect_to if url_is_safe else ""


def generate_numeric_token(length=6):
    """
    Generate a random 6 digit string of numbers.
    We use this formatting to allow leading 0s.
    """
    return get_random_string(length, allowed_chars=string.digits)


def update_is_staff(request, user):
    """Determine if the user should have `is_staff`

    Django Admin is the only use for `is_staff`

    Args:
        request: The edit request object (unused)
        user: [`User`][hypha.apply.users.models.User] to modify

    """

    if not user.is_staff and user.is_apply_staff_admin:
        user.is_staff = True
        user.save()
    elif user.is_staff and not user.is_apply_staff_admin:
        user.is_staff = False
        user.save()
