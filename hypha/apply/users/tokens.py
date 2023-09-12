from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class PasswordlessLoginTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "hypha.apply.users.tokens.PasswordlessLoginTokenGenerator"
    TIMEOUT = settings.PASSWORDLESS_LOGIN_TIMEOUT

    def check_token(self, user, token):
        """
        Check that a password reset token is correct for a given user.
        """
        if not (user and token):
            return False
        # Parse the token
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(user, ts), token):
            return False

        now = self._now()
        # Check the timestamp is within limit.
        if (self._num_seconds(now) - ts) > self.TIMEOUT:
            return False

        return True


class PasswordlessSignupTokenGenerator(PasswordlessLoginTokenGenerator):
    key_salt = "hypha.apply.users.tokens.PasswordlessSignupTokenGenerator"

    def _make_hash_value(self, user, timestamp):
        """
        Hash the signup request's primary key, email, and some user state
        that's sure to change after a password reset to produce a token that is
        invalidated when it's used:

        The token field and modified field will be updated after creating or
        updating the signup request.

        Failing those things, settings.PASSWORDLESS_LOGIN_TIMEOUT eventually
        invalidates the token.

        Running this data through salted_hmac() prevents password cracking
        attempts using the reset token, provided the secret isn't compromised.
        """
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        modified_timestamp = user.modified.replace(microsecond=0, tzinfo=None)
        return f"{user.pk}{user.token}{modified_timestamp}{timestamp}{user.email}"
