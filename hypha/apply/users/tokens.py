from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class PasswordlessLoginTokenGenerator(PasswordResetTokenGenerator):
    key_salt = "hypha.apply.users.tokens.PasswordlessLoginTokenGenerator"
    PASSWORDLESS_LOGIN_TIMEOUT = settings.PASSWORDLESS_LOGIN_TIMEOUT

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
        if (self._num_seconds(now) - ts) > self.PASSWORDLESS_LOGIN_TIMEOUT:
            return False

        return True
