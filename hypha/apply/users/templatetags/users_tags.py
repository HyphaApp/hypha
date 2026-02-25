from collections import abc
from typing import Iterable

from django import template
from django.apps import apps
from django.utils.safestring import SafeString
from django_otp import devices_for_user

from hypha.apply.users.identicon import get_identicon
from hypha.apply.users.models import User

from ..utils import can_use_oauth_check

register = template.Library()


@register.filter
def backend_name(name):
    """Human readable mapping for the social auth backend"""
    return {
        "google-oauth": "Google OAuth",
        "google-oauth2": "Google OAuth",
        "google-openidconnect": "Google OpenId",
    }.get(name, name)


@register.filter
def backend_class(backend):
    return backend.replace("-", " ")


@register.simple_tag(takes_context=True)
def can_use_oauth(context):
    user = context.get("user")

    return can_use_oauth_check(user)


@register.simple_tag
def user_2fa_enabled(user):
    """Checking if 2FA devices exist for the user"""
    if len(list(devices_for_user(user))):
        return True
    return False


@register.simple_tag
def tokens_text(token_set):
    tokens_string = ""
    for token in token_set:
        tokens_string += str(token.token) + " \n"
    return tokens_string


@register.simple_tag
def user_image(identifier: str, size=20):
    return SafeString(get_identicon(identifier, size=size))


@register.filter
def get_user_submission_count(user: User | Iterable[User]):
    ApplicationSubmission = apps.get_model("funds", "ApplicationSubmission")
    if isinstance(user, User):
        return ApplicationSubmission.objects.filter(user=user).count()
    elif isinstance(user, abc.Iterable):
        if all(isinstance(x, User) for x in user):
            return ApplicationSubmission.objects.filter(user__in=user).count()
        elif (items_extract := [x.get("item") for x in user]) and all(
            isinstance(x, User) for x in items_extract
        ):
            return ApplicationSubmission.objects.filter(user__in=items_extract).count()

    raise TypeError(
        "User instance or iterable of users not provided to get_user_submission_count!"
    )
