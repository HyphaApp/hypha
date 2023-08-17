from django.http import HttpRequest

from .utils import get_user_by_email


def send_passwordless_login_signup_email(email: str, request: HttpRequest, next_url: str = None):
    user = get_user_by_email(email)
    return user
