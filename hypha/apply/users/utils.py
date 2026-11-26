import string
import unicodedata
import zoneinfo

import nh3
from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.crypto import get_random_string
from django.utils.encoding import force_bytes
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_encode
from django.utils.translation import gettext as _
from django_ratelimit.core import _get_ip


def email_comparison_key(email) -> str:
    """Return the form of an email address used to compare it with another.

    Uses the same algorithm as Django's `_unicode_ci_compare` (used by
    `PasswordResetForm`), the one recommended by Unicode Technical Report 36,
    section 2.11.2(B)(2): NFKC normalisation followed by case folding. Unlike
    Django, surrounding whitespace is ignored too, it is never part of a valid
    address. Django's `normalize_email` only lowercases the domain, so it is
    not enough to tell whether two addresses are the same.
    """
    if not email:
        return ""
    return unicodedata.normalize("NFKC", email.strip()).casefold()


def emails_match(email_a, email_b) -> bool:
    """Return True if two email addresses are the same address."""
    key = email_comparison_key(email_a)
    return bool(key) and key == email_comparison_key(email_b)


def filter_by_email(queryset, email, field="email"):
    """Filter a queryset to the rows where `field` matches `email`.

    Works like Django's `PasswordResetForm.get_users`, plus surrounding
    whitespace is ignored: `iexact` fetches the candidates, every one is then
    checked with `emails_match`. `iexact` alone
    is not safe: PostgreSQL compares with UPPER(), and with a UTF-8 locale
    UPPER('ı') is 'I', so "bob@gmaıl.com" would match "bob@gmail.com"
    (CVE-2019-19844).
    """
    email = email.strip() if email else ""
    if not email:
        return queryset.none()
    candidates = queryset.filter(**{f"{field}__iexact": email})
    pks = [
        pk
        for pk, value in candidates.values_list("pk", field)
        if emails_match(email, value)
    ]
    return queryset.filter(pk__in=pks)


def get_user_by_email(email):
    UserModel = get_user_model()
    qs = filter_by_email(UserModel.objects.all(), email)

    # if multiple accounts then check with case sensitive search
    if len(qs) > 1:
        qs = qs.filter(email=email)  # case sensitive matching

    if len(qs) == 0:
        return

    user = qs[0]
    return user


def is_user_already_registered(email: str) -> tuple[bool, str]:
    """
    Checks if a specified user is already registered.
    Returns a tuple containing a boolean value that indicates if the user exists
    and in case he does whats the duplicated attribute
    """

    user_model = get_user_model()
    if filter_by_email(user_model.objects.all(), email).exists():
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
        whitelisted_domains = {
            *settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS,
            *settings.SOCIAL_AUTH_OKTA_OAUTH2_WHITELISTED_DOMAINS,
        }
        return domain in whitelisted_domains
    except AttributeError:
        # Anonymous user or setting not defined
        pass
    return False


def get_email_context(user=None, site=None, **extra):
    """
    Build the template context shared by the account emails: organisation
    details, plus the recipient's names and the site when given.
    """
    context = {
        "ORG_EMAIL": settings.ORG_EMAIL,
        "ORG_LONG_NAME": settings.ORG_LONG_NAME,
        "ORG_SHORT_NAME": settings.ORG_SHORT_NAME,
    }
    if user:
        context.update(
            user=user, name=user.get_full_name(), username=user.get_username()
        )
    if site:
        context.update(site=site)
    context.update(extra)
    return context


def get_other_sessions(request):
    """Yield the user's unexpired sessions, except the current one. Session data is encoded, so each one is decoded to check the user."""
    sessions = Session.objects.filter(expire_date__gt=timezone.now()).exclude(
        session_key=request.session.session_key
    )
    for session in sessions.iterator():
        if session.get_decoded().get(SESSION_KEY) == str(request.user.pk):
            yield session


def single_line(subject):
    """Force an email subject to a single line to avoid header-injection issues."""
    return "".join(subject.splitlines())


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

    timeout_minutes = settings.PASSWORD_ACTIVATION_TIMEOUT // 60

    context = get_email_context(
        user=user,
        site=site,
        activation_path=activation_path,
        timeout_minutes=timeout_minutes,
    )

    subject = single_line(render_to_string(email_subject_template, context))
    message = render_to_string(email_template, context)
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)


def send_confirmation_email(user, token, updated_email, site=None):
    """
    Send the confirmation email to the new address. The confirmation token is
    a signed payload of the requesting user's pk, their current email and the
    new email, so it only works for that user while they still hold the
    current email.
    """

    activation_path = reverse("users:confirm_email", kwargs={"token": token})

    timeout_minutes = settings.PASSWORD_RESET_TIMEOUT // 60

    context = get_email_context(
        user=user,
        site=site,
        unverified_email=updated_email,
        activation_path=activation_path,
        timeout_minutes=timeout_minutes,
    )

    subject = single_line(
        _("Confirmation email for {unverified_email} at {ORG_LONG_NAME}").format(
            **context
        )
    )
    message = render_to_string("users/email_change/confirm_email.txt", context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [updated_email])


def send_email_in_use_email(updated_email, site=None):
    """
    Notify an address that someone tried to change their account email to it,
    when it already belongs to another account.
    """
    context = get_email_context(site=site, unverified_email=updated_email)

    subject = single_line(
        _("Email change request at {ORG_LONG_NAME}").format(**context)
    )
    message = render_to_string("users/email_change/email_in_use.txt", context)
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [updated_email])


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


def login_ratelimit_key(group, request):
    """Per-account rate-limit key for the two-factor login wizard.

    The wizard prefixes its fields, so the account identifier arrives as
    `auth-username`, not `email`. The later steps (OTP, backup token) post no
    username at all, and neither do the passwordless views that share this
    decorated `dispatch` — those fall back to the client IP.

    Never return a constant for the missing-field case: django-ratelimit hashes
    whatever it is given, so every such request would land in a single bucket
    and any one client could exhaust login for everybody.
    """
    username = email_comparison_key(request.POST.get("auth-username", ""))
    return username or f"ip:{_get_ip(request)}"


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


def get_zoneinfo(tz_name):
    """Return a ZoneInfo for tz_name, or None if invalid/empty."""
    if not tz_name or len(tz_name) > 64:
        return None
    try:
        return zoneinfo.ZoneInfo(tz_name)
    except (ValueError, OSError, KeyError):
        return None


def local_event_time(request):
    """Return a human-readable "now", localised to the user's timezone.

    Shared by the account-security notification emails (login, passkey
    added/removed) so the timestamp line reads the same across them.
    """
    tz_name = (
        getattr(request, "session", {}).get("user_timezone", "") if request else ""
    )
    user_tz = get_zoneinfo(tz_name)
    return "{} ({})".format(
        formats.date_format(
            timezone.localtime(timezone=user_tz), "SHORT_DATETIME_FORMAT"
        ),
        str(user_tz) if user_tz else timezone.get_current_timezone_name(),
    )


def passkeys_enabled() -> bool:
    """Passkeys require WEBAUTHN_RP_ID in production. In DEBUG (local/dev)
    we fall back to the request host so the feature can be exercised locally.
    """
    return bool(getattr(settings, "WEBAUTHN_RP_ID", None)) or settings.DEBUG


def strip_html_and_nerf_urls(value: str):
    # Remove all HTML tags. This prohibits HTML without creating hurdles.
    cleaned_value = nh3.clean(value, tags=set())
    # Remove all colons and slashes to nerf URLs regardless of HTML tags.
    cleaned_value = cleaned_value.replace(":", "")
    cleaned_value = cleaned_value.replace("/", "")
    return cleaned_value
