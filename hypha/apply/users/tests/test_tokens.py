import pytest
from ddf import G
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from hypha.apply.users.models import PendingSignup
from hypha.apply.users.tests.factories import UserFactory

from ..tokens import (
    ActivationTokenGenerator,
    PasswordlessLoginTokenGenerator,
    PasswordlessSignupTokenGenerator,
)

# mark all test to use database
pytestmark = pytest.mark.django_db


def test_passwordless_login_token(time_machine, settings):
    """
    Test to check that the tokens are generated correctly and that they are valid
    for the correct amount of time.
    """
    settings.PASSWORDLESS_LOGIN_TIMEOUT = 60

    time_machine.move_to("2021-01-01 00:00:00", tick=False)
    # Create a token generator
    token_generator = PasswordlessLoginTokenGenerator()
    # Create a user
    user = UserFactory()
    # Create a token
    token = token_generator.make_token(user)

    # Check that the token is valid
    assert token_generator.check_token(user, token)

    # negative check
    assert token_generator.check_token(user, "invalid-token") is False

    # timeout check
    time_machine.shift(delta=62)
    assert token_generator.check_token(user, token) is False


def test_passwordless_signup_token(time_machine, settings):
    """
    Test to check that the tokens are generated correctly and that they are valid
    for the correct amount of time.
    """
    settings.PASSWORDLESS_SIGNUP_TIMEOUT = 60

    time_machine.move_to("2021-01-01 00:00:00", tick=False)

    # Create a token generator
    token_generator = PasswordlessSignupTokenGenerator()
    # Create a user
    signup_obj = G(PendingSignup)

    # Create a token
    token = token_generator.make_token(user=signup_obj)
    # Check that the token is valid
    assert token_generator.check_token(user=signup_obj, token=token)

    # negative check
    assert token_generator.check_token(signup_obj, "invalid-token") is False

    # timeout check
    time_machine.shift(delta=62)
    assert token_generator.check_token(signup_obj, token) is False


def test_activation_token_uses_activation_timeout(time_machine, settings):
    settings.PASSWORD_ACTIVATION_TIMEOUT = 60
    settings.PASSWORD_RESET_TIMEOUT = 3600

    time_machine.move_to("2021-01-01 00:00:00", tick=False)
    token_generator = ActivationTokenGenerator()
    user = UserFactory()
    token = token_generator.make_token(user)

    assert token_generator.check_token(user, token)

    time_machine.shift(delta=62)
    assert token_generator.check_token(user, token) is False


def test_activation_token_accepts_tokens_made_before_upgrade(time_machine, settings):
    """Activation links sent with Django's generator must keep working."""
    settings.PASSWORD_ACTIVATION_TIMEOUT = 60

    time_machine.move_to("2021-01-01 00:00:00", tick=False)
    user = UserFactory()
    token = PasswordResetTokenGenerator().make_token(user)

    assert ActivationTokenGenerator().check_token(user, token)
