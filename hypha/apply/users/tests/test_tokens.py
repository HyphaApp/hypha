import datetime

import pytest
from ddf import G
from freezegun import freeze_time

from hypha.apply.users.models import PendingSignup
from hypha.apply.users.tests.factories import UserFactory

from ..tokens import PasswordlessLoginTokenGenerator, PasswordlessSignupTokenGenerator

# mark this uses database
pytestmark = pytest.mark.django_db


def test_passwordless_login_token(settings):
    """
    Test to check that the tokens are generated correctly and that they are valid
    for the correct amount of time.
    """
    settings.PASSWORDLESS_LOGIN_TIMEOUT = 60

    with freeze_time("2021-01-01 00:00:00") as frozen_time:
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
        frozen_time.tick(delta=settings.PASSWORDLESS_LOGIN_TIMEOUT + 1)
        assert token_generator.check_token(user, token) is False


def test_passwordless_signup_token(settings):
    """
    Test to check that the tokens are generated correctly and that they are valid
    for the correct amount of time.
    """
    settings.PASSWORDLESS_SIGNUP_TIMEOUT = 60

    with freeze_time("2021-01-01 00:00:00") as frozen_time:
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
        frozen_time.tick(delta=datetime.timedelta(seconds=65))
        time = datetime.datetime.now()
        print(time)
        assert token_generator.check_token(signup_obj, token) is False
